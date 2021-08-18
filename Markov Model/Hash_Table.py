# CS122 W'21: Markov models and hash tables
# Rhedintza Audryna


TOO_FULL = 0.5
GROWTH_RATIO = 2


class Hash_Table:

    def __init__(self, cells, defval):
        '''
        Construct a new hash table with a fixed number of cells equal to the
        parameter "cells", and which yields the value defval upon a lookup to a
        key that has not previously been inserted

        Inputs:
            cells (int): the initial length of the hash table
            defval (str): the value that needs to be returned when key is not found
        '''
        self.table = [None] * cells
        self.defval = defval
        self.counter = 0

    def hashing(self, s):
        '''
        Takes in a string and returns a hash value

        Inputs:
            s (str): the string

        Returns:
            (int) hash value
        '''
        hash = 0
        for char in s:
            hash = hash * 37
            hash = hash + ord(char)
            hash = hash % len(self.table)

        return hash

    def lookup(self, key):
        '''
        Retrieve the value associated with the specified key in the hash table,
        or return the default value if it has not previously been inserted.

        Inputs:
            key (str): the key that wants to be looked up

        Returns:
            (str) value if found, else default value
        '''
        index = self.find_index(key)
        if not self.table[index]:
            return self.defval
        else:
            return self.table[index][1]

    def update(self, key, val):
        '''
        Change the value associated with key "key" to value "val".
        If "key" is not currently present in the hash table,  insert it with
        value "val".

        Inputs:
            key (str): the key
            val (str): the value associated with the key

        Returns:
            None, updates hash table in place
        '''
        index = self.find_index(key)

        if not self.table[index]:
            self.counter += 1
            if self.counter / len(self.table) > TOO_FULL:
                self.rehashing()

        self.table[index] = (key, val)

    def find_index(self, key):
        '''
        Returns index that corresponds to a key if it already exists, 
        or the index of an empty slot to insert the key, value pair
        if it doesn't exist yet. An empty slot here can refer to the slot
        given by index that is indicated by the hashing function, 
        or the next available empty slot

        Inputs:
            key (str): the key

        Returns:
            (int) the index
        '''
        index = self.hashing(key)

        while True:
            if (not self.table[index]) or (self.table[index][0] == key):
                return index
            index += 1
            if index == len(self.table):
                index = 0

    def rehashing(self):
        '''
        If the hash table has been filled beyond the specified ratio, 
        increases the size of the hash table and rehashes all of its
        current values

        Inputs:
            None

        Returns:
            None, modifies hash table in place
        '''
        stored_pairs = self.table[:]
        self.table = [None] * (GROWTH_RATIO * len(stored_pairs))
        self.counter = 1

        for pairs in stored_pairs:
            if pairs:
                self.update(pairs[0], pairs[1])
