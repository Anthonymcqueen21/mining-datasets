from collections import defaultdict
from itertools import combinations, chain
import sys, os, getopt
import operator


def frequentSingletons(fname, support):
    singletonFreq = defaultdict(int)
    with open(fname, "r") as f:
        numBaskets = 0
        for line in f:
            basket = set(line.split())
            numBaskets += 1
            for item in basket:
                singletonFreq[item] += 1

    for item, freq in singletonFreq.items():
        if freq < support: del singletonFreq[item]
    
    print "Singleton frequency calculated"
    return singletonFreq, numBaskets


def frequentTuples(fname, tupCandidates, ktuple, support):
    tupleFreq = dict.fromkeys(tupCandidates, 0)  
    with open(fname, "r") as f:
        for line in f:
            basket = sorted(list(set(line.split())))
            if basket and len(basket) >= ktuple:
                basketPairs = combinations(basket, ktuple)
                for itemSet in basketPairs:
                    if itemSet in tupleFreq: tupleFreq[itemSet] += 1

    for item, freq in tupleFreq.items():
        if freq < support: del tupleFreq[item]
    print ktuple,"- tuple frequency calculated."
    return tupleFreq


def candidatePairs(singletonFreq):
    allCandidates = sorted(chain(singletonFreq.keys()))
    pairCands = combinations(allCandidates, 2)
    print 'Candidate pairs found. Calculating pair frequency..'
    return pairCands


def candidateTriples(pairFreq, singletonFreq):
    tripleCands=[]
    for (elem1, elem2) in pairFreq.keys():
        for single in singletonFreq.keys():
            if tuple(sorted((single, elem1))) in pairFreq and tuple(sorted((single, elem2))) in pairFreq:
                tripleCands.append(tuple(sorted((elem1,elem2,single))))

    print 'Candidate triples found. Calculating triple frequency..'
    return tripleCands


def score(fullFreq, lhsFreq, rhsFreq, numBaskets, items, measure):
    lhsItem = items[0]
    if len(lhsItem) == 1: lhsItem = lhsItem[0]
    
    rhsItem = items[1]
    if len(rhsItem) == 1: rhsItem = rhsItem[0]
    
    fullItems = tuple(sorted(chain.from_iterable(items)))
    
    if measure == 'conf':
        return float(fullFreq[fullItems])/lhsFreq[lhsItem]
    elif measure == 'lift':
        return float(fullFreq[fullItems] * numBaskets)/(lhsFreq[lhsItem]*rhsFreq[rhsItem])
    elif measure == 'conv':
        conf = float(fullFreq[fullItems])/lhsFreq[lhsItem]
        if conf == 1: 
            return float('inf')
        else:
            return (1 - float(rhsFreq[rhsItem])/numBaskets)/(1 - conf)


def pairRuleGen(pairFreq, singletonFreq, numBaskets, measure, topN):
    rules = dict()
    for (elem1, elem2) in pairFreq.keys():
        rules[(elem1, elem2)] = score(pairFreq, singletonFreq, singletonFreq, numBaskets, ((elem1,), (elem2,)), measure)
        rules[(elem2, elem1)] = score(pairFreq, singletonFreq, singletonFreq, numBaskets, ((elem2,), (elem1,)), measure)
    
    sortedRules = sorted(rules.items(), key = operator.itemgetter(1), reverse = True)
    if measure == 'lift': sortedRules = sortedRules[::2]
    return sortedRules[:topN]


def tripleRuleGen(tripleFreq, pairFreq, singletonFreq, numBaskets, measure, topN):
    rules = dict()
    for (elem1, elem2, elem3) in tripleFreq.keys():
        rules[((elem1), (elem2, elem3))] = score(tripleFreq, singletonFreq, pairFreq, numBaskets, ((elem1,), (elem2, elem3)), measure)
        rules[((elem2), (elem1, elem3))] = score(tripleFreq, singletonFreq, pairFreq, numBaskets, ((elem2,), (elem1, elem3)), measure)
        rules[((elem3), (elem1, elem2))] = score(tripleFreq, singletonFreq, pairFreq, numBaskets, ((elem3,), (elem1, elem2)), measure)
        rules[((elem2, elem3), (elem1))] = score(tripleFreq, pairFreq, singletonFreq, numBaskets, ((elem2, elem3), (elem1,)), measure)
        rules[((elem1, elem3), (elem2))] = score(tripleFreq, pairFreq, singletonFreq, numBaskets, ((elem1, elem3), (elem2,)), measure)
        rules[((elem1, elem2), (elem3))] = score(tripleFreq, pairFreq, singletonFreq, numBaskets, ((elem1, elem2), (elem3,)), measure)
    
    sortedRules = sorted(rules.items(), key = operator.itemgetter(1), reverse = True)
    if measure == 'lift': sortedRules = sortedRules[::2]
    return sortedRules[:topN]


def printOut(topPairConf, topTripleConf, topPairLift, topTripleLift, topPairConv, topTripleConv):
    with open('apriori_out_25.txt','w') as f:
        f.write("Confidence Measure\n\n")
        f.write("2-tuple Results\n\n")
        for (elem1, elem2) in topPairConf:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')
        f.write("\n\n3-tuple Results\n\n")
        for (elem1, elem2) in topTripleConf:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')
        
        f.write("\n\n\nLift Measure\n\n")
        f.write("2-tuple Results\n\n")
        for (elem1, elem2) in topPairLift:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')
        f.write("\n\n3-tuple Results\n\n")
        for (elem1, elem2) in topTripleLift:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')
        
        f.write("\n\n\nConviction Measure\n\n")
        f.write("2-tuple Results\n\n")
        for (elem1, elem2) in topPairConv:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')
        f.write("\n\n3-tuple Results\n\n")
        for (elem1, elem2) in topTripleConv:
            f.write(str(elem1[0]) + "-->" + str(elem1[1]) + " : " + str(elem2) + '\n')



def main(argv):
    try:
        opts, args = getopt.getopt(argv, "f:s:",["file="])
    except getopt.GetoptError, err:
        print(err)
        sys.exit(2)
    
    support = False
    for opt, arg in opts:
        if opt in ("-f","--file"):
            filename = os.path.abspath(arg)
        if opt in ("-s"):
            support = arg
    
    if not support: support = 100

    singletonFreq, numBaskets = frequentSingletons(filename, support)
    pairs = candidatePairs(singletonFreq)
    #print 'pair',list(pairs)
    pairFreq = frequentTuples(filename, pairs, 2, support)
    triples = candidateTriples(pairFreq, singletonFreq)
    tripleFreq = frequentTuples(filename, triples, 3, support)
    print len(pairFreq), len(singletonFreq)
    # Confidence
    topN = 25

    topPairConf = pairRuleGen(pairFreq, singletonFreq, numBaskets, 'conf', topN)
    topTripleConf = tripleRuleGen(tripleFreq, pairFreq, singletonFreq, numBaskets, 'conf', topN)
    # Lift
    topPairLift = pairRuleGen(pairFreq, singletonFreq, numBaskets, 'lift', topN)
    topTripleLift = tripleRuleGen(tripleFreq, pairFreq, singletonFreq, numBaskets, 'lift', topN)
    # Conviction
    topPairConv = pairRuleGen(pairFreq, singletonFreq, numBaskets, 'conv', topN)
    topTripleConv = tripleRuleGen(tripleFreq, pairFreq, singletonFreq, numBaskets, 'conv', topN)
    # Output
    printOut(topPairConf, topTripleConf, topPairLift, topTripleLift, topPairConv, topTripleConv)

if __name__ == "__main__":
    main(sys.argv[1:])






















    
  
