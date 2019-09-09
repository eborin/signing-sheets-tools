#!/usr/bin/env python3 
# ---------------------------------------------------------------------------- #
#
#  Copyright (c) 2019 Edson Borin <edson@ic.unicamp.br>
#
#  This file is part of the signing-sheets-tools toolset.
# 
#  The signing-sheets-tools toolset is free software: you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License 3, as published by the Free Software Foundation.
# 
#  The signing-sheets-tools toolset is distributed in the hope that
#  it will be useful, but WITHOUT ANY WARRANTY; without even the
#  implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with the signing-sheets-tools toolset.
#  If not, see <https://www.gnu.org/licenses/>.
# 
# ---------------------------------------------------------------------------- #
 
import argparse
import os
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
from reportlab.lib import colors

def main():

    ap = argparse.ArgumentParser()
    
    ap.add_argument("-i", "--input_file", required=True,
                    help="arquivo CVS com um par RA,nome por linha")
    ap.add_argument("-o", "--output_file", required=True,
                    help="nome do arquivo de saída")
    ap.add_argument("-raf", "--RA_field", required=False, default="1",
                    help="campo do arquivo CSV que possui o RA. Padrão = 1")
    ap.add_argument("-nomef", "--nome_field", required=False, default="2",
                    help="campo do arquivo CSV que possui o nome do aluno. Padrão = 2")
    ap.add_argument("-c", "--curso", required=False, default="MC404",
                    help="nome do curso. Padrão: MC404")
    ap.add_argument("-t", "--turma", required=False, default="A/B",
                    help="string que descreve as turmas. Padrão: A/B")
    ap.add_argument("-d", "--data", required=False, default="",
                    help="string que descreve a data. Padrão: vazio")
    ap.add_argument("-ord", "--ordena", default="RA", required=False,
                    help="ordena a lista de alunos pelo ra (RA), pelo nome (nome) ou não ordena (none). Padrão: RA")
    ap.add_argument("-fn", "--formata_nome", default="abv", required=False,
                    help="Formatação dos nomes (abv, uma-linha, multiplas-linhas)")
    ap.add_argument("-ic", "--ignore_cabecalho", required=False, default="0",
                    help="ignora cabeçalho do arquivo CVS. Parâmetro é o número de linhas do cabeçalho. Padrão = 0")
    ap.add_argument("-al", "--altura_linha", required=False, default="23",
                    help="altura de cada linha em pontos. Padrão = 23")

    args = vars(ap.parse_args())

    # Read RA, Nomes from input file and generate a list of tuples (RA, Nome, "")
    print("Lendo RA e nomes do arquivo \""+args["input_file"]+"\"."+ \
          " Campo RA = "+args["RA_field"]+". Campo nome = "+args["nome_field"]+".")
    input_tuples = read_tuples(args["input_file"],int(args["RA_field"]), int(args["nome_field"]), int(args["ignore_cabecalho"]))

    # Sort list
    if args["ordena"] == "RA":
        print("Ordenando lista pelo campo RA...")
        input_tuples.sort(key=lambda tup: tup[0])
    elif args["ordena"] == "nome":
        print("Ordenando lista pelo campo nome...")
        input_tuples.sort(key=lambda tup: tup[1])
    elif args["ordena"] == "none":
        print("Mantendo a ordenação do arquivo de entrada...")
    else:
        print(args["ordena"]+" é um valor inválido para a opção ordena. Valores válidos: RA, nome, none")
        exit(1)
        
    # Initialize data with sheet header
    print("Gerando a tabela...")
    data = [('Curso',args["curso"],'Turmas',args["turma"],'Data',args["data"]),
            ('RA','Nome','Assinatura','RA','Nome','Assinatura')]

    if args["formata_nome"] == "abv":
        print("Nomes serão abreviados")
        formata_nome = abrevia_nome
    elif args["formata_nome"] == "uma-linha":
        print("Um nome completo por linha")
        formata_nome = nome_completo
    elif args["formata_nome"] == "multiplas-linhas":
        print("Nomes longos serão quebrados em múltiplas linhas")
        formata_nome = gera_funcao_quebra_linha(20)
    else:
        print("Modo de formatação de nomes inválido. Selecione entre: abv, uma-linha, multiplas-linhas.")
        exit(1)
        
    # Add two tuples per row
    row = []
    for ra, nome, ass in input_tuples:
        row.append((ra, formata_nome(nome), ass))
        if len(row) == 2:
            data.append ((row[0][0],row[0][1],row[0][2],row[1][0],row[1][1],row[1][2]))
            row = []
    if len(row) == 1:
        data.append ((row[0][0],row[0][1],row[0][2],'', '', ''))

        
    rowheights = [int(args["altura_linha"])] * len(data)
    #Cavas default? 595.27,841.89
    colwidths = [40, 95, 110]*2
    t1 = Table(data, colwidths,rowheights,repeatRows=2)
    GRID_STYLE = TableStyle(
        [('LINEABOVE', (0,0), (-1,-1), 2, colors.black),
         ('LINEBELOW', (0,0), (-1,-1), 2, colors.black),
         ('BOX', (0,0), (-1,-1), 2, colors.black), 
         ('BOX', (1,0), (-2,-1), 2, colors.black),
         ('BOX', (2,0), (-3,-1), 2, colors.black),
         ('BOX', (3,0), (-4,-1), 2, colors.black),
         ('VALIGN', (0,0), (5,-1), 'MIDDLE'),
         ('FONT', (0,1), (0,-1), 'Helvetica'),
         ('FONT', (3,1), (3,-1), 'Helvetica'), # Helvetica funcionou melhor no OCR do que courier
         ('FONTSIZE', (0,2), (5,-1), 8),
         ('FONTSIZE', (0,2), (0,-1), 9), # RA Font size
         ('FONTSIZE', (3,2), (3,-1), 9), # RA Font size
         ('GRID', (0,0), (-1,-1), 0.25, colors.black),
         ('BOTTOMPADDING',(0,0), (-1,-1), 1),
         ('ABOVEPADDING',(0,0), (-1,-1), 1),
         ('ALIGN', (0,0), (-1,-1), 'LEFT'),
         ('ALIGN', (0,0), (0,-1), 'CENTER'),
         ('ALIGN', (3,0), (3,-1), 'CENTER')
        ]
    )
    t1.setStyle(GRID_STYLE)
    lst = [t1]
    print("Gravando resultado em \""+args["output_file"]+"\".")
    SimpleDocTemplate(args["output_file"], showBoundary=0).build(lst)
      
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

# ----- #
main()
