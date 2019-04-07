import imageio
import numpy as np
import math
import argparse
import sys

from funcs import funcs


def loadbar(percent, n_blocks=15):
    percent = min(percent, 0.999999999)
    blocks = [b for b in "▏▎▍▌▋▊▉█"]
    whole = percent * n_blocks
    part = (whole - int(whole)) * len(blocks)
    return int(whole)*"█" + blocks[int(part)] + int(n_blocks - int(whole) - 1)*"-"


def process(reader, writer, delay_fn=funcs["abs"], horizontal=False, zero=0, max_delay=200, fn_args=None):
    if fn_args is None:
        fn_args = []

    W, H = reader.get_meta_data()["size"]
    fps = reader.get_meta_data()["fps"]
    
    if horizontal:
        length = W
    else:
        length = H

    delay_vec = np.vectorize(delay_fn)
    maxval = delay_vec(np.linspace(0,1,length), zero, *fn_args).max()

    scale = 1/maxval
    max_delay = int(max_delay / 1000 * fps)

    nframes = reader.count_frames()
    noutframes = nframes + max_delay
    
    buffer = None
    for i in range(noutframes):
        if i < nframes:
            f = reader.get_data(i).astype(np.float)
            if horizontal:
                f = f.transpose(1,0,2)
            if buffer is None:
                buffer = [f.copy()] * (max_delay + 2)
            buffer.append(f.copy())
        else:
            buffer.append(buffer[-1])
            
        buffer = buffer[-max_delay-2:]
        
        fnew = np.zeros_like(buffer[-1])
        for row in range(length):
            dt, dt_frac = divmod(delay_fn(row/length, zero, *fn_args)*scale*max_delay, 1)
            dt = int(dt) + 1
            fnew[row] = buffer[-dt][row] + (buffer[-dt - 1][row] - buffer[-dt][row]) * dt_frac
        if horizontal:
            fnew = fnew.transpose(1,0,2)
        writer.append_data(fnew.astype(np.uint8))

        print(f"Processing |{loadbar(i/noutframes)}| {i}/{noutframes-1}", file=sys.stderr, end="\r")
    
    print("", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Apply rolling shutter effect to video.")
    parser.add_argument("file", type=str, help="MP4 video to process")
    parser.add_argument("--horizontal", "-x", action="store_true", help="Delay along horizontal axis.")
    parser.add_argument("--zero", "-z", type=float, default=0.0, 
                        help="Position of effect's zero along chosen axis. 0 is top/left, 1 is bottom/right.")
    parser.add_argument("--delay-fn", "-f", type=str, choices=funcs.keys(), default="abs", help="Delay function.")
    parser.add_argument("--fn-args", "-F", type=float, nargs="+", help="Delay function arguments.")
    parser.add_argument("--max-delay", "-d", type=int, default=200, help="Maximum delay (in miliseconds).")

    args = parser.parse_args()

    infile = args.file
    outfile = infile.replace(".mp4", ".out.mp4")

    print(f"Reading file {infile}.")

    reader = imageio.get_reader(infile, "ffmpeg")
    fps = reader.get_meta_data()["fps"]
    writer = imageio.get_writer(outfile, fps=fps)

    print("Applying effect.")
    process(reader, writer, 
            delay_fn=funcs[args.delay_fn], 
            horizontal=args.horizontal, 
            zero=args.zero, 
            max_delay=args.max_delay, 
            fn_args=args.fn_args)
    writer.close()

    print(f"Output saved to {outfile}.")
    print("Program finished!")


if __name__ == "__main__":
    main()
