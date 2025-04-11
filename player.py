import random
import math
from hex_board import HexBoard
import time


class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id   # Tu identificador (1 o 2

    def play(self, board: HexBoard) -> tuple:
        raise NotImplementedError("¡Implementa este método!")
    

# Implementación usando MCTS con RAVE(la tranca)
class RavePlayer(Player):
    def __init__(self, player_id: int, mcts_iterations: int = 6000):
        super().__init__(player_id)
        self.mcts_iterations = mcts_iterations

    def play(self, board: HexBoard) -> tuple:
        
         for move in board.get_possible_moves():
            board_copy = board.clone()
            board_copy.place_piece(move[0], move[1], self.player_id)
            if board_copy.check_connection(self.player_id):
                return move
         root = MCTSNode(board.clone(), player_id=self.player_id)
         best_move = mcts(root, self.mcts_iterations, self.player_id)
         return best_move
    

class MCTSNode:
    def __init__(self, board: HexBoard, move=None, parent=None, player_id=None):
        self.board = board              # Estado actual del tablero
        self.move = move                # Movimiento que llevó a este estado(None en la raíz)
        self.parent = parent            # Nodo padre
        self.children = []              # Hijos(estados resultantes de movimientos)
        self.visits = 0                 # Número de visitas
        self.wins = 0                   # Número de simulaciones ganadas desde este nodo
        self.player_id = player_id      # Jugador que realizó el movimiento(1 o 2)
        self.rave_visits = {}           # move -> # de veces que apareció en un playout
        self.rave_wins = {}             # lo mismo pero las veces que ese move estuvo en un playout ganador

    def is_fully_expanded(self):
        return len(self.children) == len(self.board.get_possible_moves())

    # Ahora implementando Rapid Value Function xd
    def best_child(self, c_param=1.4, rave_const=314):
        best_score = -float('inf')
        best_child = None

        for child in self.children:
            exploitation = child.wins / child.visits
            exploration = c_param * math.sqrt(math.log(self.visits) / child.visits)

            move = child.move
            rave_visits = self.rave_visits.get(move, 0)
            rave_wins = self.rave_wins.get(move, 0)

            if rave_visits > 0:
                rave_value = rave_wins / rave_visits
            else:
                rave_value = 0

            beta =math.sqrt( rave_const /(rave_const + 3* child.visits))
            score = (1 - beta) * exploitation + beta * rave_value + exploration

            if score > best_score:
                best_score = score
                best_child = child

        return best_child


# Función de simulación aleatoria (playout)
def simulate_random_playout(board: HexBoard, current_player: int):
    board_copy = board.clone()
    player = current_player
    moves_played = []

    while True:
        possible_moves = board_copy.get_possible_moves()
        if not possible_moves:
            return 0, moves_played
        move = random.choice(possible_moves)
        board_copy.place_piece(move[0], move[1], player)
        moves_played.append((move, player)) #lo necesito pal RAVE pa tener constancia de todas las jugadas del playout
        if board_copy.check_connection(player):
            return player, moves_played
        player = 3 - player





# Función principal de MCTS
def mcts(root: MCTSNode, iterations: int, simulation_player: int, time_limit: float = 7.0):
    start_time = time.time()

    for _ in range(iterations):
        if time.time() - start_time > time_limit:
            break
        node = root
        
        # Selección
        while node.children and node.is_fully_expanded():
            node = node.best_child()

        # Expansión
        possible_moves = node.board.get_possible_moves()
        if possible_moves:
            
            tried_moves = []
            for child in node.children:
                tried_moves.append(child.move)
                
            untried_moves = []
            for move in possible_moves:
                if move not in tried_moves:
                    untried_moves.append(move)
                    
            if untried_moves:
                move = random.choice(untried_moves)
                new_board = node.board.clone()
                
                # Escogemos el jugador actual, si no tengo padre entonces soy la raiz por tanto es el simulation_player
                # En otro caso vamos switcheando
                current_player = 0
                if node.parent is None:
                    current_player = simulation_player
                else:
                    current_player = 3 - node.parent.player_id
                    
                new_board.place_piece(move[0], move[1], current_player)
                child_node = MCTSNode(new_board, move, node, current_player)
                node.children.append(child_node)
                node = child_node

        # Simulación
        simulation_result, moves_played = simulate_random_playout(node.board, 3 - node.player_id)
        
        # Backpropagation
        visited_nodes = []
        while node is not None:
            node.visits += 1
            if simulation_result == node.player_id:
                node.wins += 1

                # updateamos los valores del RAVE 
                for move, player in moves_played:
                    if player == node.player_id:
                        if move not in node.rave_visits:
                            node.rave_visits[move] = 0
                            node.rave_wins[move] = 0
                        node.rave_visits[move] += 1
                        node.rave_wins[move] += 1

            else:
                # En caso de no ganar igual me interesa guardar la info de las visitas (cambia el juego completamente)
                for move, player in moves_played:
                    if player == node.player_id:
                        if move not in node.rave_visits:
                            node.rave_visits[move] = 0
                            node.rave_wins[move] = 0
                        node.rave_visits[move] += 1
            visited_nodes.append(node)
            node = node.parent

    
    # Nos quedamos con el mejor
    best_node = None
    max_visits = -1
    for child in root.children:
        if child.visits > max_visits:
            max_visits = child.visits
            best_node = child
    return best_node.move

    #best_node = None
    #max_wins = -1

    #for child in root.children:
        #if child.wins > max_wins:
            #max_wins = child.wins
            #best_node = child

    #return best_node.move