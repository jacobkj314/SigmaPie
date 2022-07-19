import codecs
from random import choice, randint
from pprint import pprint

# #I'm also adding some more to make things easier
import pickle
def write_report(this, which):
    if which == "data":
        pickle.dump(globals()[this].data, open("results_/" + this + "/data", "wb"))
    elif which == "sample":
        pickle.dump(globals()[this+"_sample"], open("results_/" + this + "/sample", "wb"))
    elif which == "grammar":
        pickle.dump(globals()[this], open("results_/" + this + "/grammar", "wb"))
    print("recorded", which)




from sigmapie import *





class Harmony(object):
    """
    Class defining the toy generator for the harmonic datasets.
    
    Attributes:
        cl_members (dict): dictionary of the type {(harmonic_class_1):class_id_1,
            (harmonic_class_2):class_id_2, ...} that contains info about the present
            harmonic classes. Note that the transparent element can be encoded by 
            a harmonic class containing a single element.
            Example: {("a", "o"):"A", ("b", "p"):"B", ("c"):"C"}
        cl_lengths (dict): dictionary of the type {class_id:(min_len, max_len)},
            where min_len and max_len denote the min and max len of the cluster
            made out of elements of class_id.
            Example: {"A":(1, 3), "B":(2, 4), "C":(4, 8)}
        blockers (dict): dictionary of the type {"b_1":"u_1", "b_2":"u_2", ...} where
            "b" is the blocker, and "u" is the newly introduced value.
            Example: {"t":"p"}
        blocker_prob (int): a chance of observing a blocker, the P evaluates from
            (1/blocker_prob).
            Example: 5
    """
    def __init__(self, cl_members, cl_lengths = None, blockers = None, blocker_prob = 5):
        """
        Init function for the Harmony class.
        """
        self.cl_members = cl_members
        if cl_lengths is not None:
            self.cl_lengths = cl_lengths
        else:
            self.cl_lengths = {i:(1, 3) for i in self.cl_members.values()}
        self.blockers = blockers
        self.blocker_prob = blocker_prob
        

        
    def generate_words(self, n = 3, length = 10):
        """
        Generates n strings of a given length.
        
        Arguments:
            n (int): how many strings need to be generated;
            length (int): length of the strings.
            
        Returns:
            list[str]: n generated strings.
        """
        # check if the harmony rules are well-formed
        if not self._verify_classes():
            raise("Cannot generate dataset: the sets are overlapping.")
            
        # unpack the dictionary for a quicker lookup
        unpacked = self._unpack_classes()
        transparent = self._transparent()
        generated = [self._generate(unpacked, length) for i in range(n)]
        return generated
    

    def generate_pairs(self, n = 3, length = 10):
        """
        Generates n pairs of strings of a given length.
        
        Arguments:
            n (int): how many strings need to be generated;
            length (int): length of the strings.
            
        Returns:
            list[tuple[str]]: n generated pairs of strings.
        """
        transparent = self._transparent()
        outputs = self.generate_words(n, length)
        inputs = self._mask_words(outputs, transparent)
        return list(zip(inputs, outputs))
        
        
    def _generate(self, unpacked, length):
        """
        Generates a set of strings; helper function.
        
        Output type: list[str]
        """
        
        # initialize the specifications of this particular string
        string = ""
        specs = self._specify()
        
        while len(string) < length:
            
            
            # check if we can now output the blocker
            if self.blockers is not None:
                while randint(1, self.blocker_prob) == 1:
                    b = choice(list(self.blockers))
                    string += b
                    
                    if len(string) == length:
                        return string
                    
                    # rewrite the specification because of the blocker
                    if self.blockers[b] not in specs:
                        for spec in specs:
                            if unpacked[spec] == unpacked[self.blockers[b]]:
                                specs.remove(spec)
                                specs.append(self.blockers[b])
                                break
                                
            # make sure that we don't generate cluster of the same
            # harminic set as the previous one
            if len(string) > 0:
                change = string[-1] in unpacked
            else:
                change = False
            
            # select and add new possible character as many times as
            # cl_lengths indicate
            if not change:
                newchar = choice(specs)
            else:
                collection = [i for i in specs]
                collection.remove(string[-1])
                newchar = choice(collection)
            freq_b, freq_e = self.cl_lengths[unpacked[newchar]]
            string += newchar * randint(freq_b, freq_e)
            
            # output
            if len(string) > length:
                string = ""
            elif len(string) == length:
                return string
            
            
    def _mask(self, string, transparent):
        """
        Masks all non-initial mentions of the specified allophone: helper function.
        
        Output type: str
        """
        classes = {i:False for i in self.cl_members.keys()}
        undergoers = self._undergoers()
        new = ""
        for s in string:
            if (s in undergoers) and (s not in transparent.values()):
                for c in classes:
                    
                    # rewrite the non-initial mention of the harmonic set member
                    # as its harmony_class_id
                    if s in c and not classes[c]:
                        classes[c] = True
                        new += s
                    elif s in c:
                        new += self.cl_members[c]
            else:
                new += s
        return new

    
    def _mask_words(self, words, transparent):
        """
        Masks every word of a given list; helper function.
        
        Output type: list[str]
        """
        return [self._mask(w, transparent) for w in words]
            
            
    def _undergoers(self):
        """
        Collects all undergoers; helper function.
        
        Output type: list[char]
        """
        items = []
        for i in self.cl_members:
            items.extend(list(i))
        return items
    
    def _transparent(self):
        """
        Checks if there are transparent items, i.e. if there is
        a harmonic class or classes that only contain a single item.
        
        Output type: dict[str:str]
        """
        transparent = dict()
        for i in self.cl_members:
            if len(i) == 1:
                transparent[self.cl_members[i]] = i[0]
        return transparent
        
        
    def _verify_classes(self):
        """
        Verifies that no set (harmonic sets or the set of blockers)
        overlaps with each other.
        
        Output type: bool
        """
        items = self._undergoers()
        if self.blockers is not None:
            block_ok = all([i not in items for i in self.blockers])
        else:
            block_ok = True
        return len(items) == len(set(items)) and block_ok
    
    
    def _unpack_classes(self):
        """
        Creates a dictionary where every harmonizing element 
        is mapped to its harmonic class; helps to optimize 
        the lookup of this information.
        
        Output type: dict
        """
        items = self._undergoers()
        unpacked = {}
        for i in items:
            for j in self.cl_members:
                if i in j:
                    unpacked[i] = self.cl_members[j]
        return unpacked

    
    def _specify(self):
        """
        Randomly initialize a specification from all given
        harmonic datasets.
        
        Output type: list[char]
        """
        return list(map(choice, self.cl_members.keys()))





def backness_harmony(string):
    """
    Tells if a string is well-formed according to rules
    of Turkish backness harmony.
    """
    front_class, back_class = "Iaou", "ieOU"
    front, back = False, False
    
    for v in front_class + back_class:
        if v in string:
            front = True if v in front_class else front
            back = True if v in back_class else back

    return not (front and back)




def rounding_harmony(string):
    """
    Tells if a string is well-formed according to rules
    of Turkish rounding harmony.
    """
    high, low, rounded = "iIuU", "aeoO", "uUoO"
    
    vowels = "".join([v for v in string if v in high + low])
    if len(vowels) < 2:
        return True
    
    ro = vowels[0] in rounded
    
    for v in vowels[1:]:
        if v in low:
            if v in rounded:
                return False
            ro = False
        elif (ro and v not in rounded) or (not ro and v in rounded):
            return False
            
    return True




def backness_and_rounding(string):
    return backness_harmony(string) and rounding_harmony(string)




def turkish_word(length = 10, cons = "x", vowel_cluster = (1, 2),
                          cons_cluster = (0, 3)):
    """
    This generator generates fake Turkish words: namely, the words in which
    the harmonic system and rules of Turkish are preserved, but all consonants
    were substituted by a single given consonant.
    
    Arguments:
    * length (int): a length of a word that needs to be generated;
    * cons (str): a single character (or an empty string if only vowels
                  need to be generated), a "choice" of the consonant 
                  that makes this harmony long-distant;
    * vowel_cluster (tuple[int, int]): a tuple of integers representing
                                       minimal and maximal length of
                                       the vowel cluster;
    * cons_cluster (tuple[int, int]): a tuple of integers representing
                                      minimal and maximal length of
                                      the consonantal cluster.
                                      
    Returns:
    * str: a fake Turkish harmonic word, where all consonants are masked.
    """
    if length < 1:
        raise ValueError("Words cannot be so short.")
    
    vowels = {
        (True, True, True):"u",
        (True, True, False):"I",
        (True, False, True):"o",
        (True, False, False):"a",
        (False, True, True):"U",
        (False, True, False):"i",
        (False, False, True):"O",
        (False, False, False):"e"
    }
    
    backness = choice([True, False])
    height = choice([True, False])
    rounding = choice([True, False])
    
    specs = (backness, height, rounding)
    word = ""
    
    if choice([0, 1]):
            word += "x" * randint(*cons_cluster)
            
    while len(word) < length:
        vc = vowels[specs] * randint(*vowel_cluster)
        
        # this part is neededd to avoid the word-initial *oo clusters
        if len(vc) > 1 and not height and rounding:
            rounding = False
            vc = vc[0] + vowels[(backness, height, rounding)] * (len(vc) - 1)
            
        word += vc
        word += "x" * randint(*cons_cluster)
        
        height = choice([True, False])
        rounding = False if not height else rounding
        specs = (backness, height, rounding)
        
    return word[:length]




def generate_turkish_words(n = 10, length = 10, cons = "x",
                           vowel_cluster = (1, 2), cons_cluster = (1, 3)):
    """
    This generator generates a list of fake Turkish words.
    
    Arguments:
    * n (int): a number of strings that need to be generated;
    ... for the rest of the arguments, see generate_turkish_word.
    
    Outputs:
    * list: the list containing n fake Turkish words.
    """
    return [turkish_word(length, cons, vowel_cluster, cons_cluster) for i in range(n)]




def harmonic_evaluator(data, rule):
    """
    Evaluates the provided data with respect to a given
    rule of harmony.
    
    Arguments:
    * data (list[str]): a list of strings tht need to be evaluated;
    * rule (function): a function that evaluates a string according
                       to some harmony.
                       
    Results:
    * Prints the report that shows if the data follows the rule.
    """
    correct = 0
    for w in progressBar(data, prefix = "evaluating"):# #
        correct = (correct + 1) if rule(w) else correct
        
    ratio = (correct / len(data))
    print(f"Percentage of harmonic words: {int(ratio * 100)}%.")




def front_harmony(string):
    """
    Tells if a string is well-formed according to rules
    of Finnish backness harmony.
    """
    front_class, back_class = "AOy", "aou"
    front, back = False, False
    
    for v in front_class + back_class:
        if v in string:
            front = True if v in front_class else front
            back = True if v in back_class else back

    return not (front and back)




def single_harmony_no_blockers(string):
    """
    Checks if a single [a, o] harmony is well-formed.
    """
    return not("a" in string and "o" in string)




def single_harmony_with_blockers(string):
    """
    Checks if a single [a, o] harmony with a blocker f:a is well-formed.
    """
    if "f" in string:
        s1 = string[:string.index("f")]
        s2 = string[string.index("f") + 1:]
        return single_harmony_no_blockers(s1) and (not "o" in s2)
    else:
        return single_harmony_no_blockers(string)




def double_harmony(string, group = ["a", "o", "u", "e"]):
    """
    Tells if a string contains only one out of four
    (vowel) classes; check that at most one class
    of vowels occurs within one word.
    
    Arguments:
    * string (str): a string that needs to be verified;
    * group (list[char]): the harmonic class.
    """
    assert len(group) == 4
    classes = 0
    
    for i in group:
        classes = (classes + 1) if i in string else classes
        
    return classes in [0, 1]




def double_harmony_no_blockers(string):
    """
    Checks if a double [a, o] and [b, p] harmony is well-formed.
    """
    vowels = not("a" in string and "o" in string)
    consonants = not("b" in string and "p" in string)
    return vowels and consonants




def double_harmony_with_blockers(string):
    """
    Checks if a double [a, o] and [b, p] harmony with a blocker t:p
    is well-formed.
    """
    if "a" in string and "o" in string:
        return False
    
    if "t" in string:
        s1 = string[:string.index("t")]
        s2 = string[string.index("t") + 1:]
        return double_harmony_no_blockers(s1) and ("b" not in s2)
    else:
        return double_harmony_no_blockers(string)




def word_final_devoicing(sigma = ("a", "b", "p"), devoice = (("b"), ("p")),
                         length = 10, pairs = False):
    """
    This function generates either a word grammatical with respect to a rule
    of the word final devoicing, or a fake UG -> SF pair.
    
    Arguments: 
    * sigma (list[str]): a list of symbols that can be used in the words;
    * devoice (tuple[tuple, tuple]): the first tuple represents voiced
                                     obstruents, and the second one stands
                                     for their voiceless counterparts;
    * length (int): a length of the intended words;
    * pairs (bool): if True, (UG, SF) pairs will be returned, if False, only
                    the surface forms.
                    
    Outputs:
    * str/tuple: a string or a tuple of strings (depending on the parameter 
                 `pairs`) representing the application of the word-final 
                 devoicing.
    """
    if length < 1:
        raise ValueError("The string has a very weird length.")
        
    before, after = devoice
    string = "".join([choice(sigma) for i in range(length)])
    
    if string[-1] not in before:
        return (string, string) if pairs else string
    
    devoiced = string[:-1] + after[before.index(string[-1])]
    return (string, devoiced) if pairs else devoiced




def generate_wfd(n = 10, sigma = ("a", "b", "p"), devoice = (("b"), ("p")),
                 length = 10, pairs = False):
    """
    Generates a set of strings or pairs that satisfy the rule of
    the word-final devoicing.
    
    Arguments:
    * n (int): the number of strings that need to be generated;
    ... for the rest of the arguments see word_final_devoicing.
    
    Outputs:
    * list: a list of strings or tuples (depending on the parameter `pairs`)
            representing the application of the word-final devoicing.
    """
    return [word_final_devoicing(sigma, devoice, length, pairs) for i in range(n)]




def evaluate_wfd_words(data, voiced = ("b")):
    """
    Evaluates the provided words with respect to the rule 
    of the word-final devoicing.
    
    Arguments:
    * data (list[str]): a list of strings tht need to be evaluated;
    * voiced (tuple[char]): a list of voiced characters, i.e. those
                            that cannot be word-final.
                       
    Results:
    * Prints the report that shows if the data follows the ule.
    """
    correct = 0
    for w in progressBar(data, prefix = "evaluating"):# #
        
        if not len(w):
            correct += 1
            continue
            
        correct = (correct + 1) if w[-1] not in voiced else correct
        
    ratio = (correct / len(data))
    print(f"Percentage of well-formed words: {int(ratio * 100)}%.")




def generate_tonal_pattern(length = 5):
    """ Generates a random sequence of tones of a given length. """
    return "".join(choice(["H", "L"]) for i in range(length))




def utp_tones(string):
    """ Rewrites a tonal string with respect to the rules of UTP. """
    
    if set(string) not in [{"H", "L"}, {"H"}, {"L"}, set("")]:
        print(string)
        raise ValueError("Unexpected symbols in the tonal string!")
    if not ("H" in string and "L" in string):
        return string
    
    first_h = string.find("H")
    last_h = len(string) - string[::-1].find("H")
    return string[:first_h] + "H" * (last_h - first_h) + string[last_h:]




def generate_utp_strings(n = 10, length = 5):
    """ Generates n strings of tones that follow UTP rules. """
    return [utp_tones(generate_tonal_pattern(length)) for i in range(n)]




def evaluate_utp_strings(data):
    """ Evaluates the correctness of if the given sample of tonal strings. """
    correct = 0
    for w in progressBar(data, prefix = "evaluating"):# #
        correct = (correct + 1) if utp_tones(w) == w else correct
        
    ratio = (correct / len(data))
    print(f"Percentage of well-formed tonal layers: {int(ratio * 100)}%.")




def first_last_UR(n = 10, length = 10):
    """ Generates URs of first-last harmony words. """
    strings = []
    for i in range(n):
        new = choice(["a", "o"])
        new += "".join([choice(["a", "o", "x"]) for j in range(length - 2)])
        new += choice(["a", "o"])
        strings.append(new)
    return strings

def first_last(string):
    """ Makes the first and the last segment of the string the same. """
    return string[:-1] + string[0]

def first_last_words(n = 10, length = 10):
    """ Generates N first-last words. """
    return [first_last(w) for w in first_last_UR(n, length)]




def evaluate_first_last_words(data):
    """
    Evaluates the correctness of if the given sample
    of first-last harmony (UR -> SF).
    """
    newdata = [i for i in data if len(i) > 1]
    correct = 0
    for w in progressBar(newdata, prefix = "evaluating"):# #
        if w[0] == w[-1]:
            correct += 1
        
    ratio = (correct / len(newdata))
    print(f"Percentage of first-last harmonic words: {int(ratio * 100)}%.")




def generate_sp_empty_word(alphabet, length = 5):
    return "".join([choice(alphabet) for i in range(length)])

def generate_sp_empty(alphabet, n = 10, length = 5):
    return [generate_sp_empty_word(alphabet, length) for i in range(n)]




toy_wfd = generate_wfd(n = 1000)
print(toy_wfd[:15])




german_data = []
with codecs.open('german.txt', encoding='utf-8') as f:
    for line in f:
        if line != "":
            german_data.append(line[:-2])
            
print(len(german_data))
print(german_data[:10], "...")




count_final_b = 0
count_final_d = 0
count_final_g = 0

for i in german_data:
    if i[-1] == "b":
        count_final_b += 1
    elif i[-1] == "d":
        count_final_d += 1
    elif i[-1] == "g":
        count_final_g += 1
        
print("Number of final /b/:", count_final_b) # 1599, or 0.2% words
print("Number of final /d/:", count_final_d) # 15294, or 2.2% words
print("Number of final /g/:", count_final_g) # 17098, or 2.4 % words




ban = ['à', 'á', 'â', 'å', 'ç', 'è', 'é', 'ê', 'ë', 'í', 'î', 'ñ', 'ó', 'õ', 'ú',
       'û', 'č', 'ē', 'ī', 'ł', 'ō', 'œ', 'š', 'ū']

german_wfd = []
banned_words = []

for w in german_data:
    
    word = w.lower()
    
    illegal = False
    for b in ban:
        if b in word:
            banned_words.append(word)
            illegal = True
            break
            
    if illegal:
        continue
        
    if word[-1] == "b":
        word = word[:-1] + "p"
    elif word[-1] == "d":
        word = word[:-1] + "t"
    elif word[-1] == "g":
        word = word[:-1] + "k"
        
    german_wfd.append(word)

print(len(german_wfd))
print("Clean dataset:", german_wfd[:15], "...\n")

print(len(banned_words))
print("Banned words:", banned_words[:10], "...")




german_wfd_masked = []
for w in german_wfd:
    new = ""
    for s in w:
        if s in ["p", "t", "k", "b", "d", "g"]:
            new += s
        else:
            new += "a"
    german_wfd_masked.append(new)
german_data.append("")
    
print(len(german_wfd_masked))
print("Masked words:", german_wfd_masked[10:15], "...")




ts2 = {("a", "o"):"A", ("x"):"X"}
tl2 = {"A":(1, 2), "X":(2, 4)}
th2 = Harmony(ts2, tl2)
toy_vhnb = th2.generate_words(n = 1000)
print(toy_vhnb[:15], "...")




finnish_data = []
with codecs.open('finnish.txt', encoding='utf-8') as f:
    for line in f:
        if line != "":
            finnish_data.append(line[:-2])
            
print(len(finnish_data))
print(finnish_data[:10], "...")




ban = [' ', '*', '-', '.', '/', '0', '1', '2', '3', '4', '6', '8', '9', ':', '}']

finnish_harmony = []
banned_words = []
non_harmonic = []

for w in finnish_data:
    
    word = w.lower()
    
    illegal = False
    for b in ban:
        if b in word:
            banned_words.append(word)
            illegal = True
            break
            
    if illegal:
        continue
    
    word = word.replace("{", "A")
    word = word.replace("|", "O")
    if front_harmony(word):
        finnish_harmony.append(word)
    else:
        non_harmonic.append(word)

print(len(finnish_harmony))
print("Clean dataset:", finnish_harmony[105000:105015], "...\n")

print(len(banned_words))
print("Banned words:", banned_words[10:15], "...\n")

print(len(non_harmonic))
print("Non-harmonic words:", non_harmonic[:3], "...")




finnish_harmony_masked = []
for w in finnish_harmony:
    new = ""
    for s in w:
        if s in ["A", "O", "y", "a", "o", "u"]:
            new += s
        else:
            new += "x"
    finnish_harmony_masked.append(new)
    
print(len(finnish_harmony_masked))
print("Masked words:", finnish_harmony_masked[170005:170010], "...")




harmonic_classes = {("a", "o"):"A", ("x"):"X"}
blockers = {"f":"a"}
cluster_lengths = {"A":(1, 2), "X":(1, 3)}
blocker_prob = 5
h = Harmony(harmonic_classes, cluster_lengths, blockers, blocker_prob)
toy_vhwb = h.generate_words(n = 1000)
print(toy_vhwb[:15], "...")




is2 = {("a", "e", "o", "u"):"A", ("x"):"X"}
il2 = {"A":(1, 2), "X":(2, 4)}
ih2 = Harmony(is2, il2)
toy_shnb = ih2.generate_words(n = 1000)
print(toy_shnb[:15], "...")




toy_mhwb = generate_turkish_words(n = 5000, length = 8, cons_cluster = (0, 3))
toy_mhwb.extend(generate_turkish_words(n = 5000, length = 6, cons_cluster = (0, 3)))# # #Changed 3 to 4 on all cons_cluster parameters
toy_mhwb.extend(generate_turkish_words(n = 5000, length = 4, cons_cluster = (0, 3)))
print(toy_mhwb[:15], "...")




banned = []
non_harmonic = []
turkish_harmony = []

with codecs.open('turkish.txt', encoding='utf-8') as f:
    
    ban = ["!", "-", "w", "x", "A"]
    for line in f:
        if line == "":
            continue
        w = line[:-2]
        
        if any([(i in w) for i in ban]):
            banned.append(w)
            continue
            
        if backness_harmony(w) and rounding_harmony(w):
            w = w.replace("K", "k")
            turkish_harmony.append(w)
        else:
            non_harmonic.append(w)
            
print(len(banned))
print(banned[:30], "...\n")

print(len(non_harmonic))
print(non_harmonic[:30], "...\n")
            
print(len(turkish_harmony))
print(turkish_harmony[:30], "...")




turkish_harmony_masked = []
for w in turkish_harmony:
    new = ""
    for s in w:
        if s in "iIuUaeoO":
            new += s
        else:
            new += "x"
    turkish_harmony_masked.append(new)
    
print(len(turkish_harmony_masked))
print("Masked words:", turkish_harmony_masked[12005:12010], "...")




iss = {("a", "o"):"A", ("b", "p"):"B"}
ihs = Harmony(iss)
toy_dhnb = ihs.generate_words(n = 1000)
print(toy_dhnb[:15], "...")




aa = {("a", "o"):"A", ("b", "p"):"B"}
bb = {"A":(1, 2), "B":(1, 2)}
cc = {"t":"p"}
dd = 5
hmm = Harmony(aa, bb, cc, dd)
toy_dhwb = hmm.generate_words(n = 5000)
print(toy_dhwb[:15], "...")




toy_utp = generate_utp_strings(n = 1000)
print(toy_utp[:15], "...")




first_last_data = first_last_words(n = 5000)
print(first_last_data[:15], "...")














print("STARTING EXPERIMENTS")

this = "mitsl2"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = german_wfd_masked
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
evaluate_wfd_words(globals()[this+"_sample"], voiced = ("b", "d", "g"))
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




this = "mitsl3"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = german_wfd
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
evaluate_wfd_words(globals()[this+"_sample"], voiced = ("b", "d", "g"))
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




this = "mitsl5"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = finnish_harmony_masked
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
harmonic_evaluator(globals()[this+"_sample"], front_harmony)
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




this = "mitsl6"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = finnish_harmony
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
harmonic_evaluator(globals()[this+"_sample"], front_harmony)
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




this = "mitsl10"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = turkish_harmony_masked
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
harmonic_evaluator(globals()[this+"_sample"], backness_and_rounding)
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




this = "mitsl11"
print('starting', this)
globals()[this] = MITSL(polar = "n")
globals()[this].data = turkish_harmony
write_report(this, "data")
globals()[this].data.append("") # added to eliminate *>< on all tiers
globals()[this].extract_alphabet()
globals()[this].learn()
write_report(this, "grammar")
globals()[this+"_sample"] = globals()[this].generate_sample(n = 1000)
write_report(this, "sample")
harmonic_evaluator(globals()[this+"_sample"], backness_and_rounding)
'''print("--------------------------")
print("Generates such strings:", globals()[this+"_sample"][:15])
print("--------------------------")
print("Size of the grammar:", len(globals()[this].grammar))
print("--------------------------")
print("Grammars:", globals()[this].grammar)'''




