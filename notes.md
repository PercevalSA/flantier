
def load_cadeaux():
    with open(CADEAUX, 'rb') as file:
        participants = pickle.load(file)

    print("restauration de l'état de Flantier")
    return participants


    2018

[*] init participants
[*] setup impossibles
[*] setup list
[*] Go!
Marjolaine offre à Sixtine
Marc offre à Geoffroy
Geoffroy offre à Marc
Laurie-Anne offre à Loïc
Sixtine offre à Laurie-Anne
Loïc offre à Marjolaine
[*] done