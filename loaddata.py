import os,json,re
import numpy as np


def collectCardTypes(cardData):
        """This function scans through the json document and collects all instances of types, subtypes, etc. because the size and
        arrangement of our encoding will depend upon the number of each that we find.
        cardData: The json data loaded from the file."""
        
        supertypes = []
        types = []
        subtypes = []
        manaSymbols = []
        
        for cardName in cardData:
                record = cardData[cardName]
                if "supertypes" in record:
                        for super_t in record["supertypes"]:
                                if super_t not in supertypes:
                                        supertypes.append(super_t)
                if "types" in record:
                        for t in record["types"]:
                                if t not in types:
                                        types.append(t)
                
                #NOTE: I'm leaving out planeswalker subtypes for now.
                if "subtypes" in record and "Planeswalker" not in record['types']:
                        for sub_t in record["subtypes"]:
                                if sub_t not in subtypes:
                                        subtypes.append(sub_t)
                                        
                if "manaCost" in record:
                        manatxt = record["manaCost"]
                        for symbol in re.findall("(\{.*?\})",manatxt):
                                if symbol not in manaSymbols:
                                        manaSymbols.append(symbol)
                                
        supertypes.sort()
        types.sort()
        subtypes.sort()
        manaSymbols.sort()
        
        return supertypes,types,subtypes,manaSymbols
        
        

class Card(object):
        """This is our intermediate representation for cards."""
        def __init__(self, jsonEntry):
                #super(ClassName, self).__init__()
                self.name = jsonEntry['name']
                
                if 'supertypes' in jsonEntry:
                        self.supertypes = jsonEntry['supertypes']
                else:
                        self.supertypes = []
                        
                if 'types' in jsonEntry:
                        self.types = jsonEntry['types']
                else:
                        self.types = []
                        
                if 'subtypes' in jsonEntry:
                        self.subtypes = jsonEntry['subtypes']
                else:
                        self.subtypes = []
                        
                if 'power' in jsonEntry:
                        self.power = jsonEntry['power']
                else:
                        self.power = None
                        
                if 'toughness' in jsonEntry:
                        self.toughness = jsonEntry['toughness']
                else:
                        self.toughness = None
                        
                if 'manaCost' in jsonEntry:
                        self.manacost = jsonEntry['manaCost']
                else:
                        self.manacost = None
        
        def getSupertypeVector(self,supertypelist):
                """Return a 1-hot vector of card types, in the order specified by supertype list."""
                supertypeVector = np.zeros(len(supertypelist))
                for st in self.supertypes:
                        supertypeVector[supertypelist.index(t)] = 1
        
        def getTypeVector(self,typelist):
                """Return a 1-hot vector of card types, in the order specified by type list."""
                typeVector = np.zeros(len(typelist))
                for t in self.types:
                        typeVector[typelist.index(t)] = 1       
                        
        def getSubtypeVector(self,subtypelist):
                """Return a 1-hot vector of card types, in the order specified by subtype list."""
                subtypeVector = np.zeros(len(subtypelist))
                for st in self.subtypes:
                        subtypeVector[subtypelist.index(t)] = 1
                     
        def getManaCostVector(self,manaSymbolList):
                """Return a vector of indicating color identity and mana symbol counts, 
                with counts in the order specified by mana symbol list."""
                
                colorIdentity = np.zeros(5) #Order: WUBRG
                manaSymbols = np.zeros(len(manaSymbolList))
                if "W" in self.manacost:
                        colorIdentity[0] = 1
                if "U" in self.manacost:
                        colorIdentity[1] = 1
                if "B" in self.manacost:
                        colorIdentity[2] = 1
                if "R" in self.manacost:
                        colorIdentity[3] = 1
                if "G" in self.manacost:
                        colorIdentity[4] = 1
                     
                for symbol in re.findall("(\{.*?\})",self.manacost):
                        manaSymbols[manaSymbolList.index(symbol)] += 1
                
                return np.concatenate(colorIdentity,manaSymbols)
                        
        
                        
        
                
                
# filters to ignore some undesirable cards, only used when opening json
def default_exclude_sets(cardSetName):
        return cardSetName == 'Unglued' or cardSetName == 'Unhinged' or cardSetName == 'Unstable' or cardSetName == 'Celebration'

def default_exclude_types(cardtypes):
        return any( ctype in ['Conspiracy', 'Plane', 'Scheme', 'Phenomenon','Vanguard'] for ctype in cardtypes)

#def default_exclude_layouts(layout):
#        return layout in ['Token', 'Plane', 'Scheme', 'Phenomenon', 'Vanguard']
                
def getCardsFromSets(cardSets,
        exclude_sets=default_exclude_sets,
        exclude_types=default_exclude_types):
        """Collects a dictionary of uniquely named cards from all sets, with some exclusions.
        cardSets: The original format of the json data, organized by sets."""
        outputCards = {}
        
        for setCode in cardSets:
                cardSet = cardSets[setCode]
                if default_exclude_sets(cardSet['name']):
                        continue #The set is excluded from consideration.
                setCards = cardSet['cards']
                
                for card in setCards:
                        if exclude_types(card['types']) or card['name'] in outputCards:
                                #The card has a type we don't want in our dataset,
                                #or we already found another version of the same card.
                                continue 
                        else:
                                outputCards[card['name']] = card
        return outputCards

def loadCards(path):
        """Load mtgjson card data from file.
        path: The path to the json file (AllSets.json) containing all of the cards."""
        
        if not os.path.exists(path):
                raise FileExistsError("The file path {0} is invalid.".format(path))
        
        #Load the json data from the mtgjson file.
        with open(path) as cardFile: #cardFile = open(path)
                try:
                        cardSets = json.load(cardFile)
                except ValueError: #If this happens, then we're unable to read the file.
                        raise
        
        cardData = getCardsFromSets(cardSets)
        supertypes,types,subtypes,manaSymbols = collectCardTypes(cardData)
        cardObjs = [Card(cardData[entry]) for entry in cardData]
        
        print(cardData["Dismember"],cardData["Kozilek, the Great Distortion"],cardData["Barrenton Cragtreads"])
        print(cardObjs[0].getManaCostVector(manaSymbols))
        return cardObjs,supertypes,types,subtypes,manaSymbols
        
        
        
loadCards("AllSets.json")