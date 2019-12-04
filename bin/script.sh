rm -f database/database.db

python3 main.py create-class -n 2019-2s-mc404ab -f alunos-mc404AB-2019-2s.csv

for i in *-*-*.jpg ; do
    DATE=`echo $i | cut -d- -f1,2`
    echo $DATE;
    python3 main.py add-form -n 2019-2s-mc404ab -f "$i" -d $DATE;
done

python3 main.py statistics -n 2019-2s-mc404ab

#python3 main.py clear
#python3 main.py create-class -n MC404_A -f test.csv
#python3 main.py add-form -n MC404_A -f Sample1.jpg -d 08/11/2019
#python3 main.py add-form -n MC404_A -f Sample2.jpg -d 08/11/2019
#python3 main.py add-form -n MC404_A -f Sample3.jpg -d 15/11/2019
#python3 main.py add-form -n MC404_A -f Sample4.jpg -d 15/11/2019
#python3 main.py add-form -n MC404_A -f Sample5.jpg -d 22/11/2019
#python3 main.py add-form -n MC404_A -f Sample6.jpg -d 22/11/2019
#python3 main.py statistics -n MC404_A
