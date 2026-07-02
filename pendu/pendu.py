import os
import random as rd

from collections import abc
import unicodedata

# just storing a bunch of utilitaries into a class: it is a static class.
class preprocessing:
    @staticmethod
    def filter_file():
        input_file=open('noms.txt', "r")
        filtered_file=open('names_filtered.txt', "a+")
        for word in input_file:
            filtered_file.write(word.replace("\"","").replace("\n", "").replace("}","").replace(",","\n").replace("'"," "))
        input_file.close()
        filtered_file.close()

    @staticmethod
    def item_set():
        filtered_file=open('names_filtered.txt', "r")
        word_set=set()
        for line in filtered_file:
            word_set.add(line.split(" ")[2].strip())
        return word_set

    @staticmethod
    def remove_accents(text):
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

class pendu:
    @staticmethod
    def word_to_dict(word):
        return dict(enumerate(word))

    @staticmethod
    def search_index(dict, value):
        indices = [k for k, v in dict.items() if v == value]
        return indices

    @staticmethod
    def stars(word):
        return "*"*len(word)

    @staticmethod
    def putletter(letter, secret_word, indices):
        secret_word=list(secret_word)
        for i in indices:
            secret_word[i]=letter
        return ''.join(secret_word)

# Preprocessing
if not os.path.exists('names_filtered.txt'):
    preprocessing.filter_file()

word_set=preprocessing.item_set()
word_list=list(word_set)
word=rd.choice(word_list)
word=preprocessing.remove_accents(word)

# Game setup
def main():
    wordict=pendu.word_to_dict(word)
    secret_word=pendu.stars(word)
    progress=''
    tries=0
    playing=True
    print(secret_word)
    while playing:
        letter=input("Entrez une lettre: ")
        indices=pendu.search_index(wordict, letter)
        if indices:
            secret_word=pendu.putletter(letter, secret_word, indices)
            print(secret_word)
        else:
            tries+=1
            print(secret_word)
        if secret_word.count("*") == 0:
            print("Vous avez gagné!")
            playing=False
        elif tries>10:
            print("Vous avez perdu!")
            print(f"Le mot était {word}.")
            playing=False

if __name__=='__main__':
    main()


