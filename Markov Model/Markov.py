# CS122 W'21: Markov models and hash tables
# Rhedintza Audryna

import sys
import math
import Hash_Table

HASH_CELLS = 57


class Markov:

    def __init__(self, k, s):
        '''
        Construct a new k-order Markov model using the statistics of string "s"
        '''
        self.k = k
        self.table = Hash_Table.Hash_Table(HASH_CELLS, 0)
        self.unique_chars = len(set(s))
        self.learn(s)

    def learn(self, s):
        '''
        Collects information about the frequencies of characters, 
        and the contexts in which they appear. 

        Inputs:
            s (str): the  string

        Returns:
            None, modifies the model in place
        '''

        prev = s[-self.k:]

        for char in s:
            self.table.update(prev, self.table.lookup(prev) + 1)

            seq = prev + char
            self.table.update(seq, self.table.lookup(seq) + 1)

            prev = seq[1:]

    def log_probability(self, s):
        '''
        Get the log probability of string "s", given the statistics of
        character sequences modeled by this particular Markov model
        This probability is *not* normalized by the length of the string.
        '''

        prev = s[-self.k:]
        all_prob = 0

        for char in s:
            seq = prev + char
            seq_count = self.table.lookup(seq)
            prev_count = self.table.lookup(prev)
            prob = math.log((seq_count + 1) / (prev_count + self.unique_chars))
            all_prob += prob
            prev = seq[1:]

        return all_prob


def identify_speaker(speech1, speech2, speech3, order):
    '''
    Given sample text from two speakers (1 and 2), and text from an
    unidentified speaker (3), return a tuple with the *normalized* 
    log probabilities of each of the speakers
    uttering that text under a "order" order character-based Markov model,
    and a conclusion of which speaker uttered the unidentified text
    based on the two probabilities.
    '''

    model_1 = Markov(order, speech1)
    model_2 = Markov(order, speech2)

    length = len(speech3)
    prob_1 = model_1.log_probability(speech3) / length
    prob_2 = model_2.log_probability(speech3) / length

    if prob_1 > prob_2:
        likely = 'A'
    else:
        likely = 'B'

    return (prob_1, prob_2, likely)


def print_results(res_tuple):
    '''
    Given a tuple from identify_speaker, print formatted results to the screen
    '''
    (likelihood1, likelihood2, conclusion) = res_tuple

    print("Speaker A: " + str(likelihood1))
    print("Speaker B: " + str(likelihood2))

    print("")

    print("Conclusion: Speaker " + conclusion + " is most likely")


if __name__ == "__main__":
    num_args = len(sys.argv)

    if num_args != 5:
        print("usage: python3 " + sys.argv[0] + " <file name for speaker A> " +
              "<file name for speaker B>\n  <file name of text to identify> " +
              "<order>")
        sys.exit(0)

    with open(sys.argv[1], "r") as file1:
        speech1 = file1.read()

    with open(sys.argv[2], "r") as file2:
        speech2 = file2.read()

    with open(sys.argv[3], "r") as file3:
        speech3 = file3.read()

    res_tuple = identify_speaker(speech1, speech2, speech3, int(sys.argv[4]))

    print_results(res_tuple)
