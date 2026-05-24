_AGC1 = 4885
_AGC2 = 2450
_AGC3 = 1700
_SHORT = 340
_LONG = 680
_SILENCE = 5057

class MarkisolCommand:
    def __init__(self, data32: int) -> None:
        b0 = (data32 >>  0) & 0xFF
        b1 = (data32 >>  8) & 0xFF
        b2 = (data32 >> 16) & 0xFF
        b3 = (data32 >> 24) & 0xFF

        sum     = (b0 + b1 + b2 + b3) % 256
        cheksum = (1 - sum) % 256

        self.bits = (
            format(data32, "032b")[::-1] +
            format(cheksum, "08b")[::-1] +
            "1"
        )

    def encode(self) -> list[int]:
        """Convert self.bits to a signed alternating-µs timing list.

        Positive values are marks (high/on); negative are spaces (low/off).
        Adjacent same-sign pulses at bit boundaries are merged.
        """
        result: list[int] = []
        pending: int | None = None

        def add(v: int) -> None:
            nonlocal pending
            if pending is None:
                pending = v
            elif (v > 0) == (pending > 0):
                pending += v
            else:
                result.append(pending)
                pending = v

        add(_AGC1); add(-_AGC2); add(_AGC3)
        for bit in self.bits:
            if bit == "0":
                add(-_SHORT); add(_SHORT); add(-_SHORT)
            else:
                add(-_SHORT); add(_LONG)
        add(-_SILENCE)

        if pending is not None:
            result.append(pending)
        return result
