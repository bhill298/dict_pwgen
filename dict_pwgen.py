#!/usr/bin/env python3
import argparse
import glob
import os
import random
import string
import sys


def read_words(f, delimiter):
    return set(f.read().split(delimiter))


def word_filter(word, args):
    is_valid = True
    if len(word) >= args.min_wordlen and len(word) <= args.max_wordlen:
        is_valid = True
        if is_valid and not args.allow_space:
            is_valid = ' ' not in word
        if is_valid and not args.allow_hyphen:
            is_valid = '-' not in word
        return is_valid
    return False


def true_with_prob(p):
    # techincally this can return exactly 0 (0.0 <= X < 1.0)
    if p <= 0.0:
        return False
    return random.random() < p


def trans_word(word, trans_table, args):
    chars = []
    if args.always_upper_start:
        chars.append(word[0].upper())
        word = word[1:]
    for c in word:
        if true_with_prob(args.trans_modify_prob):
            c = random.choice(trans_table.get(c, [c]))
        if true_with_prob(args.upper_modify_prob):
            # this can trigger again after the symbol replacement, will just do nothing
            c = c.upper()
        chars.append(c)
    return ''.join(chars)


def get_password_crack_times(pw):
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "zxcvbn-python"))
    from zxcvbn import zxcvbn

    results = zxcvbn(pw)
    output = []
    output.append("Crack times:")
    col_size = max(len(key) for key in results["crack_times_display"]) + 1
    for key, value in results["crack_times_display"].items():
        key = key.replace('_', ' ').title()
        value = value.title()
        output.append(f"{key:<{col_size}}: {value}")
    return '\n'.join(output)


def relpath(fname):
    return os.path.join(os.path.dirname(__file__), fname)


def prob_arg(prob):
    try:
        prob = float(prob)
        if prob < 0.0 or prob > 1.0:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Probability should be a valid number from [0, 1] got {prob}")
    return prob


def positive_int_arg(i, disallow_zero=False):
    try:
        i = int(i)
        if i < 0 or (disallow_zero and i == 0):
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Should be a valid int >{'' if disallow_zero else '='} 0, got {i}")
    return i
positive_int_arg_nonzero = lambda i: positive_int_arg(i, disallow_zero=True)


parser = argparse.ArgumentParser(description="Generate passwords using dictionary words that are easier to remember")
parser.add_argument('-i', "--input-dict", type=argparse.FileType('r'), default=[], action="append", help="use custom wordlist (can be passed multiple times)")
parser.add_argument('-I', "--input-glob", type=str, default=[], action="append", help="custom wordlist(s) as a glob (can be passed multiple times and combined with -i)")
parser.add_argument('-d', "--delimiter", default='\n', help="word delimiter for input files (default: newline)")
parser.add_argument('-m', "--min-wordlen", type=positive_int_arg, default=6, help="min length of words to use (default: %(default)s)")
parser.add_argument('-a', "--max-wordlen", type=positive_int_arg_nonzero, default=float("inf"), help="max length of words to use (default: no max)")
parser.add_argument('-n', "--num-words", type=positive_int_arg_nonzero, default=4, help="number of words to generate (default: %(default)s)")
parser.add_argument('-N', "--num-pwds", type=positive_int_arg_nonzero, default=1, help="number of passwords to generate (default: %(default)s)")
parser.add_argument('-y', "--allow-hyphen", action="store_true", help="allow words with hyphens")
parser.add_argument('-p', "--allow-space", action="store_true", help="allow words with spaces")
parser.add_argument('-t', "--trans-modify-prob", type=prob_arg, default=0.0,
    help="transform characters in words with some probability [0, 1] (e.g. 'a' -> @) (default: %(default)s)")
parser.add_argument('-u', "--upper-modify-prob", type=prob_arg, default=0.0,
    help="uppercase characters in words with some probability [0, 1] (default: %(default)s)")
parser.add_argument('-U', "--always-upper-start", action="store_true",
    help="always make first character of each word uppercase (skips all other modifications for that character)")
parser.add_argument('-c', "--add-char-prob", type=prob_arg, default=1.0,
    help="add number + symbols with some probability [0, 1] (default: %(default)s)")
parser.add_argument('-w', "--add-char-where", choices=("between", "beforeafter", "everywhere"), default="between",
    help="where to add numbers + symbols (between words, before and after words, everywhere - including between characters) (default: %(default)s)")
parser.add_argument('-r', "--crack-times", action="store_true", help="print estimate crack times for generated password (using zxcvbn)")
parser.add_argument('-R', "--check-crack-times", default=None, help="give a password to check crack times for rather then generating a new one.")
args = parser.parse_args()

if args.check_crack_times is not None:
    print(get_password_crack_times(args.check_crack_times))
    sys.exit(0)

if args.max_wordlen < args.min_wordlen:
    raise ValueError(f"max wordlen should not be < min wordlen ({args.max_wordlen} < {args.min_wordlen})")

symbols = "!@#$%^&_-?.,~\"'()*+/:;<>=`|"
symbols_digits = string.digits + symbols
trans_table = {
    's': ['5', '$'],
    'a': ['@'],
    't': ['7'],
    'l': ['1'],
    'o': ['0'],
    'b': ['8'],
    'g': ['9'],
    'e': ['3'],
    'i': ['!'],
}

input_files = []
if args.input_dict or args.input_glob:
    for f in args.input_dict:
        input_files.append(f)
    for g in args.input_glob:
        for fname in glob.glob(g):
            if os.path.isfile(fname):
                input_files.append(open(fname))
else:
    input_filenames = [os.path.join("wordlists", el) for el in ["words.txt"]]
    for fname in input_filenames:
        input_files.append(open(relpath(fname)))

words = set()
for f in input_files:
    words = words.union(read_words(f, args.delimiter))
    f.close()
words = list({word for word in words if word_filter(word, args)})
if len(words) < args.num_words:
    raise ValueError(f"Filtered wordlist has {len(words)} unique elements, which is too short for password length {args.num_words}")

for pwd_it in range(args.num_pwds):
    selection = random.sample(words, k=args.num_words)
    final_words = []
    for idx, word in enumerate(selection):
        last_word = idx == len(selection) - 1
        word = word.lower()
        word = trans_word(word, trans_table, args)
        if args.add_char_prob > 0.0:
            word_list = []
            for i in range(len(word) + 1):
                do_insert = False
                if args.add_char_where == "between":
                    do_insert = i == len(word) and not last_word
                elif args.add_char_where == "beforeafter":
                    do_insert = i == 0 or i == len(word)
                elif args.add_char_where == "everywhere":
                    do_insert = True

                if do_insert and true_with_prob(args.add_char_prob):
                    word_list.append(random.choice(symbols_digits))
                if i < len(word):
                    word_list.append(word[i])
            word = ''.join(word_list)
        final_words.append(word)
    pw = ''.join(final_words)

    print(pw)
    if args.crack_times:
        print(get_password_crack_times(pw))
        if args.num_pwds > 1 and pwd_it < args.num_pwds - 1:
            print()
