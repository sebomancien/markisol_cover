# Markisol Cover — Home Assistant Custom Integration

Home Assistant custom integration for Markisol/BY-305 RF-motorized blinds. Commands are transmitted at 433.92 MHz OOK via an ESPHome RF transmitter connected to Home Assistant.

## BY-305 RF Protocol

The BY-305 (sold as BF-305 in the Markisol ecosystem) uses a proprietary OOK protocol at **433.92 MHz**. Each frame is 41 bits long and is repeated **40 times** per command for reliability.

### Frame structure (wire bit order)

```
 0              15 16  19 20  23 24      31 32      39 40
 ┌────────────────┬──────┬──────┬──────────┬──────────┬───┐
 │   Remote ID    │  CH  │ CMD  │ Model ID │ Checksum │ T │
 │   (16 bits)    │(4 b) │(4 b) │ (8 bits) │ (8 bits) │(1)│
 └────────────────┴──────┴──────┴──────────┴──────────┴───┘
```

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| Remote ID | 0–15 | 16 | Arbitrary identifier chosen at pairing time. |
| Channel | 16–19 | 4 | Selects which channel (see table below). |
| Command | 20–23 | 4 | Action to perform (see table below). |
| Model ID | 24–31 | 8 | Identifies the remote model. `10000000` (0x80) for BY-305 / BF-305. |
| Checksum | 32–39 | 8 | Integrity check (see below). |
| Trailing | 40 | 1 | Always `1`. Purpose unknown. |

All fields are transmitted **LSB first**.

### Channel encoding (wire values)

| Channel | Wire bits (LSB first) |
|---------|-----------------------|
| 1 | `1000` |
| 2 | `0100` |
| 3 | `1100` |
| 4 | `0010` |
| 5 | `1010` |
| All | `1111` |

### Command encoding (wire values)

| Action | Wire bits (LSB first) |
|--------|-----------------------|
| Open (UP) | `0011` |
| Close (DOWN) | `1000` |
| Stop | `1010` |

### Checksum

The 8-bit checksum is computed over the four data bytes `b0..b3`, where `b0` is the least-significant byte of the 32-bit data word and `b3` is the most-significant:

```
checksum = (1 - (b0 + b1 + b2 + b3)) mod 256
```

The checksum is then transmitted LSB first, like all other fields.

### Example frame

Remote ID `0xF74F`, channel 1, command OPEN, model 0x80:

```
Remote ID        CH    CMD   Model ID  Checksum  T
1111001011101111 1000  0011  10000000  10011111  1
```

## Bit-level Wire Encoding

Each data bit is encoded as a sequence of high (mark) and low (space) pulses. All durations are in microseconds.

### Bit patterns

| Data bit | Wire sequence | Timing |
|----------|--------------|--------|
| `0` | LOW → HIGH → LOW | 340 µs, 340 µs, 340 µs |
| `1` | LOW → HIGH | 340 µs, 680 µs |

Adjacent same-polarity pulses at bit boundaries are merged into a single pulse, so the raw timing list is shorter than `41 × 3` elements.

### Preamble (AGC sequence)

Transmitted before the 41 data bits to allow the receiver's AGC to lock on:

```
HIGH 4885 µs → LOW 2450 µs → HIGH 1700 µs
```

### Frame termination

```
LOW 5057 µs
```

### Full single-frame timing diagram

```
     AGC                      bit 0            bit 1
  ┌───────┐     ┌─────┐  ┌─┐ ┌─┐  ┌───┐  ┌─┐ ┌───┐
  │ 4885  │2450 │1700 │  │ │ │ │  │   │  │ │ │   │
──┘       └─────┘     └──┘ └─┘ └──┘   └──┘ └─┘   └─ ···
                       340 340 340   340  340 680
```


## Implementation

### Module overview

| File | Responsibility |
|------|---------------|
| `markisol.py` | Low-level protocol: builds the 41-bit frame and converts it to raw OOK timings. |
| `remote.py` | Protocol field constants (`Channel`, `Command` enums), model ID, `RemoteCommand` encoder/decoder. |
| `cover.py` | Home Assistant cover entity: maps HA service calls to `RemoteCommand` → `MarkisolCommand` → RF transmission. |
| `config_flow.py` | Integration setup UI: remote ID, model ID, channel. |

### Stored constant values

| Field | Wire value | Stored value |
|-------|-----------|--------------|
| Model ID BY-305 | `10000000` | `0x01` |
| Channel 1 | `1000` | `0x1` |
| Channel 2 | `0100` | `0x2` |
| Channel 3 | `1100` | `0x3` |
| Channel 4 | `0010` | `0x4` |
| Channel 5 | `1010` | `0x5` |
| All channels | `1111` | `0xF` |
| OPEN | `0011` | `0xC` |
| CLOSE | `1000` | `0x1` |
| STOP | `1010` | `0x5` |
