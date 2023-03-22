#!/usr/bin/env python3
import argparse
import math
import os
import random
import string
import sys


def read_words(fname, delimiter="\n"):
    with open(fname) as f:
        return set(f.read().split(delimiter))


def word_filter(word, args):
    if len(word) >= args.min_wordlen and len(word) <= args.max_wordlen:
        if not args.allow_hyphen:
            return '-' not in word
    return False


def trans_word(word, trans_table, args):
    chars = []
    if args.always_upper_start:
        chars.append(word[0].upper())
        word = word[1:]
    for c in word:
        if random.random() < args.trans_modify_prob:
            c = random.choice(trans_table.get(c, [c]))
        if random.random() < args.upper_modify_prob:
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


parser = argparse.ArgumentParser(description="Generate passwords using dictionary words that are easier to remember")
parser.add_argument('-s', "--sciterms", action="store_true", help="use science terms dictionary")
parser.add_argument('-j', "--jargon", action="store_true", help="use jargon (names / proper nouns, more complex words) dictionary")
parser.add_argument('-m', "--min-wordlen", type=int, default=0, help="min length of words to use")
parser.add_argument('-a', "--max-wordlen", type=int, default=float("inf"), help="max length of words to use")
parser.add_argument('-n', "--num-words", type=int, default=4, help="number of words to generate")
parser.add_argument('-y', "--allow-hyphen", action="store_true", help="allow words with hyphens")
parser.add_argument('-t', "--trans-modify-prob", type=float, default=0.0, help="transform characters in words with some probability [0, 1] (e.g. 'a' -> @)")
parser.add_argument('-u', "--upper-modify-prob", type=float, default=0.0, help="uppercase characters in words with some probability [0, 1]")
parser.add_argument('-U', "--always-upper-start", action="store_true", help="always make first character of each word uppercase (skips all other modifications)")
parser.add_argument('-c', "--add-char-prob", type=float, default=0.0, help="add number + symbols with some probability [0, 1]")
parser.add_argument('-w', "--add-char-where", choices=("between", "beforeafter", "everywhere"), default="between",
    help="where to add numbers + symbols (between words, before and after words, everywhere - including between characters)")
parser.add_argument('-r', "--crack-times", action="store_true", help="Print estimate crack times for generated password (using zxcvbn)")
parser.add_argument('-R', "--check-crack-times", default=None, help="Give a password to check crack times for rather then generating a new one.")
args = parser.parse_args()

if args.check_crack_times is not None:
    print(get_password_crack_times(args.check_crack_times))
    sys.exit(0)

if args.max_wordlen < 0:
    raise ValueError(f"max wordlen should not be < 0, got {args.max_wordlen}")
if args.min_wordlen < 0:
    raise ValueError(f"min wordlen should not be < 0, got {args.min_wordlen}")
if args.max_wordlen < args.min_wordlen:
    raise ValueError(f"max wordlen should not be < min wordlen ({args.max_wordlen} < {args.min_wordlen})")
if args.trans_modify_prob < 0.0 or args.trans_modify_prob > 1.0:
    raise ValueError(f"trans prob should be in [0, 1], got {args.trans_modify_prob}")
if args.upper_modify_prob < 0.0 or args.upper_modify_prob > 1.0:
    raise ValueError(f"upper prob should be in [0, 1], got {args.upper_modify_prob}")
if args.add_char_prob < 0.0 or args.add_char_prob > 1.0:
    raise ValueError(f"add char prob should be in [0, 1], got {args.add_char_prob}")

symbols = "!@#$%^&_-?.,~"
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

words = read_words("words.txt")
if args.sciterms:
    words = words.union(read_words("science-terms.txt"))
if args.jargon:
    words = words.union(read_words("jargon.txt"))
words = list({word for word in words if word_filter(word, args)})
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

            if do_insert and random.random() < args.add_char_prob:
                word_list.append(random.choice(symbols_digits))
            if i < len(word):
                word_list.append(word[i])
        word = ''.join(word_list)
    final_words.append(word)
pw = ''.join(final_words)
print(pw)
if args.crack_times:
    print()
    print(get_password_crack_times(pw))
