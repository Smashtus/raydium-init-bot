LAMPORTS_PER_SOL = 1_000_000_000

def sol_to_lamports(x: float) -> int:
    return int(round(x * LAMPORTS_PER_SOL))

def lamports_to_sol(x: int) -> float:
    return x / LAMPORTS_PER_SOL
