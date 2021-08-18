# CS122: Auto-completing keyboard using Tries
# Distribution
#
# Matthew Wachs
# Autumn 2014
#
# Revised: August 2015, AMR
#   December 2017, AMR
#
# Rhedintza Audryna

import os
import sys
from sys import exit

import autocorrect_shell


class EnglishDictionary(object):
    def __init__(self, wordfile):
        '''
        Constructor

        Inputs:
          wordfile (string): name of the file with the words.
        '''
        self.words = TrieNode()

        with open(wordfile) as f:
            for w in f:
                w = w.strip()
                if w != "" and not self.is_word(w):
                    self.words.add_word(w)

    def is_word(self, w):
        '''
        Is the string a word?

        Inputs:
           w (string): the word to check

        Returns: boolean
        '''

        if self.words.last_node(w):
            return self.words.last_node(w).final
        else:
            return False

    def num_completions(self, prefix):
        '''
        How many words in the dictionary start with the specified
        prefix?

        Inputs:
          prefix (string): the prefix

        Returns: int
        '''

        if self.words.last_node(prefix):
            return self.words.last_node(prefix).count
        else:
            return 0

    def get_completions(self, prefix):
        '''
        Get the suffixes in the dictionary of words that start with the
        specified prefix.

        Inputs:
          prefix (string): the prefix

        Returns: list of strings.
        '''

        last_node = self.words.last_node(prefix)

        if last_node:
            if last_node.final:
                return [''] + last_node.trie_to_words('')
            else:
                return [] + last_node.trie_to_words('')
        else:
            return []


class TrieNode(object):
    def __init__(self):
        '''
        Constructor for a TrieNode
        '''

        self.count = 0
        self.final = False
        self.children = {}

    def add_word(self, word):
        '''
        Adds a word to the trie

        Inputs:
            word (string): the word to be added
        '''

        self.count += 1

        if not word:
            self.final = True
        else:
            self.children[word[0]] = self.children.get(word[0], TrieNode())
            self.children[word[0]].add_word(word[1:])

    def last_node(self, prefix):
        '''
        Returns the node for the last letter in the prefix,
        if it exists

        Inputs:
            prefix (string): the prefix

        Returns: (object) TrieNode if exists, None otherwise
        '''

        if not prefix:
            return self

        else:
            if prefix[0] in self.children:
                return self.children[prefix[0]].last_node(prefix[1:])
            else:
                return None

    def trie_to_words(self, prev):
        '''
        A list of final words for a given Trie node

        Inputs:
          prev (str): the previous letter

        Returns: list of strings
        '''

        one_down = []
        children = []

        for letter, node in self.children.items():
            if self.children[letter].final:
                one_down.append(prev + letter)
            children += node.trie_to_words(prev + letter)
        return one_down + children


if __name__ == "__main__":
    autocorrect_shell.go("english_dictionary")
