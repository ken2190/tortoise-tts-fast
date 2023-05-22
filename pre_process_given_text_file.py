import re
import argparse

# Constants
split_length = 125

def split_sentences(text):
    # Split the text into sentences using regex
    return re.split(r'(?<=[.!?])\s+', text)

def merge_sentences(sentences):
    merged_sentences = []
    current_sentence = sentences[0]
    
    for next_sentence in sentences[1:]:
        if len(current_sentence) + len(next_sentence) + 1 <= split_length:
            current_sentence += ' ' + next_sentence
        else:
            merged_sentences.append(current_sentence)
            current_sentence = next_sentence
    merged_sentences.append(current_sentence)
    return merged_sentences

def process_sentence(sentence, split_length):
    if len(sentence) > split_length:
        if ',' in sentence[:split_length]:
            split_index = sentence[:split_length].rfind(',')
        else:
            split_index = sentence[:split_length].rfind(' ') + 1

        sentence_parts = [sentence[:split_index].strip(), sentence[split_index + 1:].strip()]
        return '; '.join(sentence_parts)
    else:
        return sentence.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, default='speech.txt', help="Input file name")
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as file:
        text = file.read().replace('"', '').replace('\n', ' ')

    # Replace double spaces with single spaces
    text = re.sub(r'\s{2,}', ' ', text)

    sentences = split_sentences(text)
    merged_sentences = merge_sentences(sentences)
    processed_sentences = [process_sentence(sentence, split_length) for sentence in merged_sentences]

    merged_text = ';'.join(processed_sentences)
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

    with open('processed_speech.txt', 'w', encoding='utf-8') as file:
        file.write(merged_text)

    print(f"Processed text saved to 'processed_speech.txt'")

if __name__ == "__main__":
    main()
