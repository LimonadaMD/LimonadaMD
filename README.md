# limonada
LIpid Membranes Open Network And DAtabase


__Installation__

1. git clone https://github.com/LimonadaMD/LimonadaMD.git
2. pip install requirements/dev.txt
3. apt-get install sqlite3 openbabel
4. sqlite3 db.sqlite3 < db.sqlite3.txt
5. python2.7 manage.py migrate 
6. python2.7 manage.py runserver

__Configuration__

When a topology is added to the database, a verification is made with gromacs to check its validity.
Add gromacs bin path at the end of limonada/settings/base.py



