from hanabi import *
import util
import agent
import random

def format_hint(h):
    if h == HINT_COLOR:
        return "color"
    return "rank"

#builds off the outer agent
class Hanabit(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):
        # TBH not sure what this top part does. Maybe remembering what hints we gave?
        # answer given: yes it does help with remembering
        for player,hand in enumerate(hands):
            for card_index,_ in enumerate(hand):
                if (player,card_index) not in self.hints:
                    self.hints[(player,card_index)] = set()
        known = [""]*5
        for h in self.hints:
            pnr, card_index = h 
            if pnr != nr:
                known[card_index] = str(list(map(format_hint, self.hints[h])))
        self.explanation = [["hints received:"] + known]
        
        my_knowledge = knowledge[nr]
        
        # we should have some more aggressive plays here
        potential_discards = []
        probabilities = []
        for i,k in enumerate(my_knowledge):
            # if a card is 100% playable, early termination just to be safe
            if util.is_playable(k, board):
                return Action(PLAY, card_index=i)
            # for every card in hand, compute the probability that this card is playable
            p = util.probability(util.playable(board), k) 
            probabilities.append(p)
            # if a card is 100% useless, early termination just to be safe
            if util.is_useless(k, board):    
                potential_discards.append(i)
  
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))
        
        # if nothing is for sure, play the most playable card when there is still room for error
        # we can adjust how confident we are about the probability
        if hits > 1 and max(probabilities) >= 0.6:
            return Action(PLAY, card_index=probabilities.index(max(probabilities)))
        elif cards_left <= 5 and max(probabilities) >= 0.8:
            return Action(PLAY, card_index=probabilities.index(max(probabilities)))

        #From here on out if we couldn't guarantee a play or discard we look to give hints
        playables = []        
        for player,hand in enumerate(hands):
            if player != nr:
                for card_index,card in enumerate(hand):
                    if card.is_playable(board):                              
                        playables.append((player,card_index))
        
        playables.sort(key=lambda which: -hands[which[0]][which[1]].rank)
        while playables and hints > 0:
            player,card_index = playables[0]
            knows_rank = True
            real_color = hands[player][card_index].color
            real_rank = hands[player][card_index].rank
            k = knowledge[player][card_index]
            
            hinttype = [HINT_COLOR, HINT_RANK]
            
            for h in self.hints[(player,card_index)]:
                hinttype.remove(h)
            
            # as of right now chooses a random hint...
            # may not be the best course of action doe
            # changed it to be kind of selective...
            # chooses the hint that gives the most playable cards
            # believe this might be the safer path and avoids hints that may
            # cause mistakes
            t = None
            if hinttype:
                # if hinttype is size one then just hint it
                if len(hinttype) == 1:
                    t = hinttype[0]
                else:
                    # else we choose the hint that gives us more playable cards
                    playableR = 0
                    playableC = 0
                    for i,card in enumerate(hands[player]):
                        if card.rank == hands[player][card_index].rank and card.is_playable(board):
                            playableR += 1
                        if card.color == hands[player][card_index].color and card.is_playable(board):
                            playableC += 1
                    
                    if playableR > playableC:
                        t = HINT_RANK
                    elif playableR == playableC:
                        t = HINT_RANK
                    else:
                        t = HINT_COLOR
            
            if t == HINT_RANK:
                for i,card in enumerate(hands[player]):
                    if card.rank == hands[player][card_index].rank:
                        self.hints[(player,i)].add(HINT_RANK)
                return Action(HINT_RANK, player=player, rank=hands[player][card_index].rank)
            if t == HINT_COLOR:
                for i,card in enumerate(hands[player]):
                    if card.color == hands[player][card_index].color:
                        self.hints[(player,i)].add(HINT_COLOR)
                return Action(HINT_COLOR, player=player, color=hands[player][card_index].color)
            
            playables = playables[1:]
 
        # not sure what this does either...
        # is this for remembering hints?
        # answer given: yes it does help with remembering
        if hints > 0:
            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
            hintgiven = random.choice(hints)
            if hintgiven.type == HINT_COLOR:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.color == hintgiven.color:
                        self.hints[(hintgiven.player,i)].add(HINT_COLOR)
            else:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.rank == hintgiven.rank:
                        self.hints[(hintgiven.player,i)].add(HINT_RANK)
                
            return hintgiven
        
        # instead of discarding a random card if nothing else better to do, discard the least playable card
        return Action(DISCARD, card_index=probabilities.index(min(probabilities)))
        
        # return random.choice(util.filter_actions(DISCARD, valid_actions))

    def inform(self, action, player):
        if action.type in [PLAY, DISCARD]:
            if (player,action.card_index) in self.hints:
                self.hints[(player,action.card_index)] = set()
            for i in range(5):
                if (player,action.card_index+i+1) in self.hints:
                    self.hints[(player,action.card_index+i)] = self.hints[(player,action.card_index+i+1)]
                    self.hints[(player,action.card_index+i+1)] = set()

agent.register("hanabit", "First ever agent", Hanabit)
