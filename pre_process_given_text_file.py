#Base on tutorial of FurkanGozukara, i rewrite this script to split text more efficiently
#https://github.com/FurkanGozukara/Stable-Diffusion/blob/main/Tutorials/Deep-Voice-Clone-Tutorial-Tortoise-TTS.md
import re, subprocess, sys
import argparse
try:
    import spacy
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy'])
    import spacy
	
# Constants
split_length = 125
nlp = None

def split_sentences(text):
    # Split the text into sentences using regex
    return re.split(r'(?<=[.!?])\s+', text)


def find_split_point(line, words, split_length):
    for word in words:
        if word in line and line.index(word) < split_length:
            return line.rindex(word, 0, split_length + 1)
    return split_length

def pre_clean(text):
    formated_text = text.replace('"', '').replace('\n', ' ')

    # Replace double spaces with single spaces
    formated_text = re.sub(r'\s{2,}', ' ', text)


    return formated_text

def split_text(nlp, text):
    pre_clean(text)
    sentences = split_sentences(text)

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    split_lines = []
    current_line = ""
    current_char_count = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current_char_count + sentence_len <= split_length:
            current_line += " " + sentence
            current_char_count += sentence_len
        else:
            split_lines.append(current_line.strip())
            current_line = sentence
            current_char_count = sentence_len

    if current_line:
        split_lines.append(current_line.strip())

    split_words = [".", ",", " und ", " oder ", " and ", " or "]

    final_split_lines = []
    for line in split_lines:
        while len(line) > split_length:
            split_point = find_split_point(line, split_words, split_length)
            final_split_lines.append(line[:split_point].strip())
            line = line[split_point + 1:].strip()

        final_split_lines.append(line.strip())

    return final_split_lines


def post_clean(lines):
    merged_text = ';'.join(lines)
    merged_text = re.sub(r';{2,}', ';', merged_text)
    merged_text = merged_text.replace('; ', ';')
    merged_text = merged_text.replace("’", "'")
    merged_text = merged_text.replace(';', '\n')

    # Remove special characters reserved in .bat files
    reserved_characters = ['<', '>', '/', '\\', '|', '*']
    for char in reserved_characters:
        merged_text = merged_text.replace(char, '')

    # Limit the total length to 8000 characters
    if len(merged_text) > 7900:
        merged_text = merged_text[:7900]

    return merged_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, default='speech.txt', help="Input file name")
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    lines = split_text(nlp, text)

    merged_text = post_clean(lines)

    with open('processed_speech.txt', 'w', encoding='utf-8') as file:
        file.write(merged_text)

    print(f"Processed text saved to 'processed_speech.txt'")


if __name__ == "__main__":
    try:
        nlp = spacy.load("de_dep_news_trf")
    except:
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'de_dep_news_trf'])
        nlp = spacy.load("de_dep_news_trf")
    # try:
    #    en = spacy.load("en_core_web_trf")
    # except:
    #    subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_trf'])

    main()
