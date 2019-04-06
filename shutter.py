import imageio
import numpy as np
import math
import argparse
import sys


def loadbar(percent, n_blocks=15):
    percent = min(percent, 0.999999999)
    blocks = [b for b in "▏▎▍▌▋▊▉█"]
    whole = percent * n_blocks
    part = (whole - int(whole)) * len(blocks)
    return int(whole)*"█" + blocks[int(part)] + int(n_blocks - int(whole) - 1)*"-"


def main():
    funcs = {"abs": lambda x, zero: abs(x-zero), 
             "quad": lambda x, zero: (x-zero)**2, 
             "quadlog": lambda x, zero: math.log10((x-zero)**2 + 1), 
             "sin": lambda x, zero: math.sin(2*math.pi * (x-zero)*2)**2}

    parser = argparse.ArgumentParser(description="Apply rolling shutter effect to video.")
    parser.add_argument("file", type=str, help="MP4 video to process")
    parser.add_argument("--horizontal", "-x", action="store_true", help="Effect axis.")
    parser.add_argument("--zero", "-z", type=float, default=0.0, 
                        help="Position of effect's zero along chosen axis. 0 is top/left, 1 is bottom/right.")
    parser.add_argument("--delay-fn", "-f", type=str, choices=funcs.keys(), default="abs", help="Delay scaling function.")
    parser.add_argument("--max-delay", "-d", type=int, default=200, help="Maximum delay (in miliseconds).")

    args = parser.parse_args()

    infile = args.file
    outfile = infile.replace(".mp4", ".out.mp4")

    print(f"Reading file {infile}.")

    reader = imageio.get_reader(infile, "ffmpeg")
    meta = reader.get_meta_data()
    W, H = meta["size"]
    fps = meta["fps"]
    writer = imageio.get_writer(outfile, fps=fps)

    horizontal = args.horizontal

    if horizontal:
        length = W
    else:
        length = H

    if 0 <= args.zero <= 1:
        zero = args.zero
    else:
        raise Exception("The 'zero' value must be between 0 and 1.")

    delay_fn = funcs[args.delay_fn]
    delay_vec = np.vectorize(delay_fn)
    maxval = delay_vec(np.linspace(0,1,length), zero).max()

    scale = 1/maxval
    maxdelay = int(args.max_delay / 1000 * fps)

    nframes = reader.count_frames()
    noutframes = nframes + 2*maxdelay
    buffer = None

    print("Applying effect.")

    for i in range(noutframes):
        if i < nframes:
            f = reader.get_data(i).astype(np.float)
            if horizontal:
                f = f.transpose(1,0,2)
            if buffer is None:
                buffer = [f.copy()] * (maxdelay + 2)
            buffer.append(f.copy())
        else:
            buffer.append(buffer[-1])
            
        buffer = buffer[-maxdelay-2:]
        
        fnew = np.zeros_like(buffer[-1])
        for row in range(length):
            dt, dt_frac = divmod(delay_fn(row/length, zero)*scale*maxdelay, 1)
            dt = int(dt) + 1
            fnew[row] = buffer[-dt][row] + (buffer[-dt - 1][row] - buffer[-dt][row]) * dt_frac
        if horizontal:
            fnew = fnew.transpose(1,0,2)
        writer.append_data(fnew.astype(np.uint8))

        print(f"Processing |{loadbar(i/noutframes)}| {i}/{noutframes-1}", file=sys.stderr, end="\r")
    
    writer.close()
    print("", file=sys.stderr)

    print(f"Output saved to {outfile}.")
    print("Program finished!")

if __name__ == "__main__":
    main()
