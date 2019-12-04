import argparse
import os
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Spacer
from reportlab.lib import colors

DEFAULT_HEADER_ROW_HEIGHT = 23

def generate(inputFile, outputFile, curso, turma="A/B", raField=1, nameField=2, ordena="RA", nameFormat="abv", ignoreHeader=0, rowHeight=45):
    # Read RA, Nomes from input file and generate a list of tuples (RA, Nome, "")
    print("Lendo RA e nomes do arquivo \""+inputFile+"\"."+ \
          " Campo RA = "+str(raField)+". Campo nome = "+str(nameField)+".")
    input_tuples = read_tuples(inputFile, raField, nameField, ignoreHeader)

    # Sort list
    if ordena == "RA":
        print("Ordenando lista pelo campo RA...")
        input_tuples.sort(key=lambda tup: tup[0])
    elif ordena == "nome":
        print("Ordenando lista pelo campo nome...")
        input_tuples.sort(key=lambda tup: tup[1])
    elif ordena == "none":
        print("Mantendo a ordenação do arquivo de entrada...")
    else:
        print(ordena+" é um valor inválido para a opção ordena. Valores válidos: RA, nome, none")
        exit(1)
        
    # Initialize data with sheet header
    print("Gerando a tabela...")
    header_data = [('Curso: {}'.format(curso),'Turmas: {}'.format(turma),'Data: ')]

    if nameFormat == "abv":
        print("Nomes serão abreviados")
        formata_nome = abrevia_nome
    elif nameFormat == "uma-linha":
        print("Um nome completo por linha")
        formata_nome = nome_completo
    elif nameFormat == "multiplas-linhas":
        print("Nomes longos serão quebrados em múltiplas linhas")
        formata_nome = gera_funcao_quebra_linha(20)
    else:
        print("Modo de formatação de nomes inválido. Selecione entre: abv, uma-linha, multiplas-linhas.")
        exit(1)
        
    # Add two tuples per row
    row = []
    second_header_data = [('RA','Nome','Assinatura','RA','Nome','Assinatura')]
    data = []
    for ra, nome, ass in input_tuples:
        row.append((ra, formata_nome(nome), ass))
        if len(row) == 2:
            data.append ((row[0][0],row[0][1],row[0][2],row[1][0],row[1][1],row[1][2]))
            row = []
    if len(row) == 1:
        data.append ((row[0][0],row[0][1],row[0][2],'', '', ''))

    rowheights = [rowHeight] * len(data)
    
    header_colwidths = [135, 150, 285]
    main_colwidths = [40, 95, 150]*2

    data = second_header_data + data
    rowheights.insert(0, DEFAULT_HEADER_ROW_HEIGHT)

    t1 = Table(header_data, header_colwidths, DEFAULT_HEADER_ROW_HEIGHT, repeatRows=0)
    t2 = Table(data, main_colwidths, rowheights, repeatRows=1)
    HEADER_GRID_STYLE = TableStyle(
        [('LINEABOVE', (0,0), (-1,-1), 2, colors.black),
         ('LINEBELOW', (0,0), (-1,-1), 2, colors.black),
         ('BOX', (0,0), (-1,-1), 2, colors.black), 
         ('BOX', (1,0), (-2,-1), 2, colors.black),
         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
         ('FONT', (0,0), (-1,-1), 'Helvetica'),
         ('FONTSIZE', (0,0), (-1,-1), 10),
         ('GRID', (0,0), (-1,-1), 0.25, colors.black),
         ('BOTTOMPADDING',(0,0), (-1,-1), 1),
         ('ABOVEPADDING',(0,0), (-1,-1), 1),
         ('ALIGN', (0,0), (-1,-1), 'LEFT')
        ]
    )
    MAIN_GRID_STYLE = TableStyle(
        [('LINEABOVE', (0,0), (-1,-1), 2, colors.black),
         ('LINEBELOW', (0,0), (-1,-1), 2, colors.black),
         ('BOX', (0,0), (-1,-1), 2, colors.black), 
         ('BOX', (1,0), (-2,-1), 2, colors.black),
         ('BOX', (2,0), (-3,-1), 2, colors.black),
         ('BOX', (3,0), (-4,-1), 2, colors.black),
         ('VALIGN', (0,0), (5,-1), 'MIDDLE'),
         ('FONT', (0,0), (-1,-1), 'Helvetica'),
         ('FONT', (3,1), (3,-1), 'Helvetica'), # Helvetica funcionou melhor no OCR do que courier
         ('FONTSIZE', (0,0), (-1,0), 9), # Header Font Size
         ('FONTSIZE', (1,1), (1,-1), 9), # Name Font Size
         ('FONTSIZE', (4,1), (4,-1), 9), # Name Font Size
         ('FONTSIZE', (0,1), (0,-1), 10), # RA Font size
         ('FONTSIZE', (3,1), (3,-1), 10), # RA Font size
         ('GRID', (0,0), (-1,-1), 0.25, colors.black),
         ('BOTTOMPADDING',(0,0), (-1,-1), 1),
         ('ABOVEPADDING',(0,0), (-1,-1), 1),
         ('ALIGN', (0,0), (-1,-1), 'LEFT'),
         ('ALIGN', (0,0), (0,-1), 'CENTER'),
         ('ALIGN', (3,0), (3,-1), 'CENTER')
        ]
    )
    t1.setStyle(HEADER_GRID_STYLE)
    t2.setStyle(MAIN_GRID_STYLE)
    lst = [t1, Spacer(0,20), t2]
    print("Gravando resultado em \""+outputFile+"\".")
    SimpleDocTemplate(outputFile, showBoundary=0).build(lst)

    return input_tuples
      
def abrevia_nome(nome):
    nomes = nome.split()
    if len(nomes) == 1 : return nome
    abv = nomes[0]
    for n in nomes[1:-1]: abv += " " + n[0] + "."
    abv += " " + nomes[-1]
    return abv

def nome_completo(nome):
    nomes = nome.split()
    n = nomes[0]
    for i in nomes[1:]: n += " " + i
    return n

def read_tuples(input_filename, raf, nomef, header_lines):
    fh = open(input_filename, "r")
    input_tuples = []
    while True:
        s = fh.readline().split(',')
        if header_lines > 0:
            header_lines -= 1
        else:
            if len(s) < raf or len(s) < nomef: break
            input_tuples.append((s[raf-1],s[nomef-1],''))
    fh.close()
    return input_tuples

def gera_funcao_quebra_linha(max_chars):
    def quebralinhas(nome):
        nomes = nome.split()
        n = nomes[0]
        count_chars = len(n)
        for i in nomes[1:]:
            if count_chars + len(i) > max_chars:
                n += "\n"
                count_chars = 0
            n += " " + i
            count_chars += len(i) + 1
        return n
    return quebralinhas
