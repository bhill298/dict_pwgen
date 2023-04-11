#!/usr/bin/env python3
import argparse
import os


def in_file(f, delimiter):
    out = set()
    for word in f.read().split(delimiter):
        word = word.strip().lower()
        if len(word) > 0:
            out.add(word)
    return out


def out_file(name, s, delimiter):
    num_words = len(s)
    # If newline is not specified, \n is written out as \r\n on Windows
    with open(name, 'x', newline='') as f:
        f.write(delimiter.join(sorted(s)))
        print(f"Writing {name} with {num_words} words")
        return num_words


def get_output_name(inname):
    base, ext = os.path.splitext(inname)
    return base + ".new" + ext


parser = argparse.ArgumentParser(description="Process word lists, removing duplicate words (output files will be based on input file names).")
parser.add_argument("infiles", metavar="infile", type=argparse.FileType('r'), nargs='+', help="input file names")
parser.add_argument('-d', "--outdir", default=os.path.curdir, help="text file output dir")
parser.add_argument('-i', "--input-delimiter", default='\n', help="delimiter of input files")
parser.add_argument('-o', "--output-delimiter", default='\n', help="delimiter of output files")
parser.add_argument('-c', "--combine", action="store_true", help="combine all output files into one (name will be based on the first input file)")
args = parser.parse_args()

if not os.path.isdir(args.outdir):
    raise ValueError(f"Output dir {args.outdir} is not a valid directory")
# (filename, dataset)
infiles = []
all_input_words = set()

for f in args.infiles:
    dataset = in_file(f, args.input_delimiter)
    dataset = dataset.difference(all_input_words)
    all_input_words.update(dataset)
    infiles.append((f.name, dataset))
    f.close()

print(f"Total unique input words: {len(all_input_words)}")

if args.combine:
    out_file(get_output_name(infiles[0][0]), all_input_words, args.output_delimiter)
else:
    for fname, dataset in infiles:
        out_file(get_output_name(fname), dataset, args.output_delimiter)