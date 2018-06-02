import os,json,re
import pandas as pd, numpy as np, tensorflow as tf
from abc import ABC, abstractmethod


class CardDataIterator():
        """This is the iterator we use to assemble cards into batches for training."""
        def __init__(self, cards):
                self.cards = cards
                self.size = len(self.cards)
                self.epochs = 0
                self.shuffle()
                
        def shuffle(self):
                self.df = self.df.sample(frac=1).reset_index(drop=True)
                self.cursor = 0
                
        def next_batch(self, n):
                if self.cursor+n-1 > self.size:
                        self.epochs += 1
                        self.shuffle()
                res = self.df.ix[self.cursor:self.cursor+n-1]
                self.cursor += n
                
                
class CardDataFormatter(ABC):
        """This is the abstract base class for card data formatters.
        You can write your own subclasses that implement your own formatting
        strategy."""
        def __init__(self):
                """The abstract constructor for the formatter class."""
                
        @abstractmethod
        def format(self,card):
                """This method converts the card into a form that we can feed to our network."""
                pass


class SimpleTextFormatter(CardDataFormatter):
        """This is the default, barebones text formatter."""
        def __init__(self,vocab,includeFields=["name","supertypes","types","subtypes","manacost","rarity","power","toughness","text"]):
                """
                includeFields: The fields we will include in our output as text.
                vocab: The vocab that we will use to map symbols in card text to numbers.
                """
                self.vocab = vocab
                self.includeFields = includeFields
                super().__init__()
                        
        def format(self,card):
                output = "|"
                for field in self.includeFields:
                        try:
                                value = getattr(card,field)
                        except AttributeError:
                                print("Formatting Failure! Unrecognized card field: {0}".format(field))
                                raise
                        if isinstance(value, list):
                                value = ' '.join(value)         
                        output += ("{0}|".format(value))
                return output


class HintVectorFormatter(CardDataFormatter):
        """This formatter allows you to set aside fields (e.g. types, mana costs) that will be passed
           to the network at each timestep as a vector rather than having it predict those fields."""
        def __init__(self,typeList,supertypeList,subtypeList,manaSymbolList,vocab,includeFields=["name","supertypes","types","subtypes","manacost","rarity","power","toughness","text"],hintFields=[]):
                """
                typeList: The list of types among cards in our dataset.
                supertypeList: The list of supertypes among cards in our dataset.
                subtypeList: The list of subtypes among cards in our dataset.
                manaSymbolList: The list of mana symbols in costs among cards in our dataset.
                vocab: The vocab that we will use to map symbols in card text to numbers.
                includeFields: The fields we will include in our output as text.
                hintFields: The fields we will represent in our hint vector.
                """
                self.typeList = typelist
                self.supertypeList = supertypelist
                self.subtypeList = subtypelist
                self.manaSymbolList = manaSymbolList
                self.vocab = vocab
                self.includeFields = includeFields
                super().__init__()
        
        def format(self,card):
                pass
        
        
        def __getSupertypeVector(self,card):
                """Return a 1-hot vector of card types, in the order specified by supertype list."""
                supertypeVector = np.zeros(len(self.supertypelist))
                for st in card.supertypes:
                        supertypeVector[self.supertypelist.index(t)] = 1
                return supertypeVector
        
        def __getTypeVector(self,card):
                """Return a 1-hot vector of card types, in the order specified by type list."""
                typeVector = np.zeros(len(self.typelist))
                for t in card.types:
                        typeVector[self.typelist.index(t)] = 1
                return typeVector   
                        
        def __getSubtypeVector(self,card):
                """Return a 1-hot vector of card types, in the order specified by subtype list."""
                subtypeVector = np.zeros(len(self.subtypelist))
                for st in card.subtypes:
                        subtypeVector[self.subtypelist.index(t)] = 1
                return subtypeVector
                     
        def __getManaCostVector(self,card):
                """Return a vector of indicating color identity and mana symbol counts, 
                with counts in the order specified by mana symbol list."""
                
                colorIdentity = np.zeros(5) #Order: WUBRG
                manaSymbols = np.zeros(len(self.manaSymbolList))
                if "W" in card.manacost:
                        colorIdentity[0] = 1
                if "U" in card.manacost:
                        colorIdentity[1] = 1
                if "B" in card.manacost:
                        colorIdentity[2] = 1
                if "R" in card.manacost:
                        colorIdentity[3] = 1
                if "G" in card.manacost:
                        colorIdentity[4] = 1
                     
                for symbol in re.findall("(\{.*?\})",card.manacost):
                        manaSymbols[self.manaSymbolList.index(symbol)] += 1
                
                return np.concatenate(colorIdentity,manaSymbols)

        

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
                        
                if 'rarity' in jsonEntry:
                        self.rarity = jsonEntry['rarity']
                else:
                        self.rarity = None                        
                        
                if 'text' in jsonEntry:
                        self.text = jsonEntry['text']
                else:
                        self.text = None
                        
        
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
        

def default_exclude_sets(cardSetName):
        """Filters out undesirable sets."""
        return cardSetName == 'Unglued' or cardSetName == 'Unhinged' or cardSetName == 'Unstable' or cardSetName == 'Celebration'

def default_exclude_types(cardtypes):
        """Filters out cards with undesirable types."""
        return any( ctype in ['Conspiracy', 'Plane', 'Scheme', 'Phenomenon','Vanguard'] for ctype in cardtypes)

#def default_exclude_layouts(layout):
#        return layout in ['Token', 'Plane', 'Scheme', 'Phenomenon', 'Vanguard']
                
def getCardsFromSets(cardSets,exclude_sets=default_exclude_sets,exclude_types=default_exclude_types):
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
        
class JSONDataSanitizer():
        """This class encapsulates all the logic that we need to sanitize the JSON data prior to processing it with our framework."""
        def __init__(self):
                pass
                
        def __removeReminderText(self,jsonData):
                if 'text' in jsonData:
                        text = jsonData['text']
                        for reminder in re.findall("(\\(.*\\))",text):
                                text = text.replace(reminder,'')
                        jsonData['text'] = text
                        
        def __replaceNameWithSymbol(self,jsonData,symbol='@'):
                if 'name' in jsonData and 'text' in jsonData:
                        text = jsonData['text']
                        name = jsonData['name']
                        text = text.replace(name,symbol)
                        jsonData['text'] = text
                        
                
        def sanitize(self,jsonData):
                self.__removeReminderText(jsonData)
                self.__replaceNameWithSymbol(jsonData)
                return jsonData
                
        

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
        
        sanitizer = JSONDataSanitizer()
        for entry in cardData:
                cardData[entry] = sanitizer.sanitize(cardData[entry])
        
        supertypes,types,subtypes,manaSymbols = collectCardTypes(cardData)
        cardObjs = [Card(cardData[entry]) for entry in cardData]
        
        print(cardData["Dismember"],cardData["Kozilek, the Great Distortion"],cardData["Barrenton Cragtreads"])
        formatter = SimpleTextFormatter(vocab=None)
        print(formatter.format(cardObjs[0]))
        print(formatter.format(cardObjs[1]))
        print(formatter.format(cardObjs[2]))
        
        return cardObjs,supertypes,types,subtypes,manaSymbols
        
        
        
loadCards("AllSets.json")
#print("Hello World!")