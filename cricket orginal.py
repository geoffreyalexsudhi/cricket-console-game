import random
import mysql.connector
import time
import tabulate
import sys

l7=[1,2]

def choice():
    while True:
        try:
            ch1=int(input("Enter choice number: "))
            if ch1 in l7:
                return ch1
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\n---Game ended---")
            sys.exit()
        except ValueError:
            print("Enter choice number only\nTry again")
        except Exception as err:
            print("An error has occurred:",err)

def database():
    global my,db
    try:
        db=mysql.connector.connect(host="localhost",user="root",password=m2)
        my=db.cursor()
        my.execute("CREATE DATABASE IF NOT EXISTS cricket")
        my.execute("USE cricket")
        my.execute("""CREATE TABLE IF NOT EXISTS user(
Username VARCHAR(250) PRIMARY KEY,
Games_played INTEGER,
No_of_wins INTEGER,
No_of_draws INTEGER,
No_of_losses INTEGER,
Runs_scored INTEGER,
Last_game VARCHAR(7))""")
        user()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        sys.exit()
    except KeyboardInterrupt:
        print("\n---Game ended---")
        sys.exit()

def replay():
    print("Do you want to play again?")
    print("1.Yes")
    print("2.No")
    k3=choice()
    if k3==1:
        print("\n-------Previous game ended-------")
        time.sleep(1)
        print("-------New game starting-------\n")
        if not db.is_connected():
            database()
            return
        game()
    else:
        print("\n-------Game ended-------")
        if db.is_connected():
            db.close()
        sys.exit()

def user():
    my.execute("SELECT Username FROM user")
    rec=my.fetchall()
    l5=[]
    for i in rec:
        l5.append(i[0])
    if m3 not in l5:
        print("New user")
        print("Welcome {}".format(m3))
        my.execute("INSERT INTO user VALUES(%s,0,0,0,0,0,NULL)",(m3,))
        db.commit()
        game()
    else:
        print("Welcome back {}".format(m3))
        play()

def res(sum1,sum3):
    print("Match over")
    my.execute("SELECT * FROM user WHERE Username=%s",(m3,))
    l6=my.fetchone()
    if l6 is None:
        print("User not found")
        return
    gp=l6[1]+1
    rs=l6[5]+sum1
    try:
        if sum1>sum3:
            print("You won by",sum1-sum3,"runs")
            nr=l6[2]+1
            my.execute("""UPDATE user SET Games_played=%s,No_of_wins=%s,
Runs_scored=%s,Last_game=%s WHERE Username=%s""",
            (gp,nr,rs,"Win",m3))
            db.commit()
        elif sum1<sum3:
            print("Computer won by",sum3-sum1,"runs")
            nr1=l6[4]+1
            my.execute("""UPDATE user SET Games_played=%s,No_of_losses=%s,
Runs_scored=%s,Last_game=%s WHERE Username=%s""",
            (gp,nr1,rs,"Lose",m3))
            db.commit()
        else:
            print("Draw")
            nr3=l6[3]+1
            my.execute("""UPDATE user SET Games_played=%s,No_of_draws=%s,
Runs_scored=%s,Last_game=%s WHERE Username=%s""",
            (gp,nr3,rs,"Draw",m3))
            db.commit()
    except mysql.connector.Error as err:
        print("An error has occurred")
        print(err)
        db.rollback()
    replay()

def play():
    print("1.Would you like to play a match?")
    print("2.Would you like to see previous scores?")
    m1=choice()
    if m1==1:
        game()
    elif m1==2:
        my.execute("SELECT * FROM user WHERE Username=%s",(m3,))
        rec=my.fetchall()
        table=tabulate.tabulate(
            rec,
            headers=['Username','Games_played','No_of_wins','No_of_draws',
                     'No_of_losses','Runs_scored','Last_game'],
            tablefmt="grid")
        print(table)
        print("1.Would you like to play the game now?")
        print("1.Yes")
        print("2.No")
        m0=choice()
        if m0==1:
            game()
        else:
            print("---Game ended---")
            sys.exit()

def game():
    print("Starting match")
    print("1.Odd")
    print("2.Even")
    k=choice()
    d=0
    e=0
    k7=0
    k1=0
    sum1=0
    sum3=0

    while True:
        try:
            a=int(input("Enter number between 0 and 6: "))
            if 0<=a<=6:
                break
            print("Invalid choice")
        except KeyboardInterrupt:
            print("---Game ended---")
            sys.exit()
        except ValueError:
            print("Enter number only\nTry again")

    b=random.randrange(0,7)
    print("The number entered by the computer",b)
    c=a+b

    if c%2==0:
        print("The sum is even")
        d+=1
    else:
        print("The sum is odd")
        e+=1

    if (k==1 and e==1) or (k==2 and d==1):
        print("You won the toss")
        print("1.Batting")
        print("2.Balling")
        k1=choice()
        while True:
            try:
                w1=int(input("Enter number of wickets (recommended small number): "))
                if w1>0:
                    break
                print("Invalid number of wickets")
            except ValueError:
                print("Enter number only")
            except KeyboardInterrupt:
                print("---Game ended---")
                sys.exit()
        w2=w1
    else:
        print("Computer won the toss")
        k7=random.randrange(1,3)
        if k7==1:
            print("Computer decided to bat")
        else:
            print("Computer decided to ball")
        w1=random.randrange(1,3)
        print("The number wicket is",w1)
        w2=w1

    def start(k1,k7):
        if k1==1:
            print("You are batting")
            u(w1,sum1,sum3,w2)
        elif k1==2:
            print("Computer is batting")
            comp(w2,sum3,sum1,w1)
        elif k7==2:
            print("You are batting")
            u(w1,sum1,sum3,w2)
        elif k7==1:
            print("Computer is batting")
            comp(w2,sum3,sum1,w1)
        else:
            print("Error")
            sys.exit()

    def u(w1,sum1,sum3,w2):
        while w1>0:
            try:
                q=int(input("Enter number between 0 and 6: "))
                if q>6 or q<0:
                    print("Error: Enter valid number")
                    print("Run is not counted")
                    print("Try again")
                    continue
                z=random.randrange(0,7)
                print("The number entered by the computer is:",z)
                if sum1>=200:
                    print("Maximum runs taken")
                    break
                elif q==z:
                    print("--Out--")
                    w1-=1
                    if w1>0:
                        print("--Next wicket starting--")
                else:
                    sum1+=q
            except KeyboardInterrupt:
                print("---Game ended---")
                sys.exit()
            except ValueError:
                print("Enter number only\nTry again")
            except Exception as err:
                print("An error has occurred:",err)

        print("Total runs",sum1)
        print("Computer is batting")

        while w2>0:
            try:
                q=int(input("Enter number between 0 and 6: "))
                if q>6 or q<0:
                    print("Error: Enter valid number")
                    print("Run is not counted")
                    print("Try again")
                    continue
                z=random.randrange(0,7)
                print("The number entered by the computer is:",z)
                if sum3>=200:
                    print("Maximum runs taken")
                    break
                elif q==z:
                    print("--Out--")
                    w2-=1
                    if w2>0:
                        print("--Next wicket starting--")
                else:
                    sum3+=z
                    if sum3>sum1:
                        break
            except KeyboardInterrupt:
                print("---Game ended---")
                sys.exit()
            except ValueError:
                print("Enter number only\nTry again")
            except Exception as err:
                print("An error has occurred:",err)

        print("Total runs",sum3)
        res(sum1,sum3)

    def comp(w2,sum3,sum1,w1):
        while w2>0:
            try:
                q=int(input("Enter number between 0 and 6: "))
                if q>6 or q<0:
                    print("Error: Enter valid number")
                    print("Run is not counted")
                    print("Try again")
                    continue
                z=random.randrange(0,7)
                print("The number entered by the computer is:",z)
                if sum3>=200:
                    print("Maximum runs taken")
                    break
                elif q==z:
                    print("--Out--")
                    w2-=1
                    if w2>0:
                        print("--Next wicket starting--")
                else:
                    sum3+=z
            except KeyboardInterrupt:
                print("---Game ended---")
                sys.exit()
            except ValueError:
                print("Enter number only\nTry again")
            except Exception as err:
                print("An error has occurred:",err)

        print("Total runs",sum3)
        print("You are batting")

        while w1>0:
            try:
                q=int(input("Enter number between 0 and 6: "))
                if q>6 or q<0:
                    print("Error: Enter valid number")
                    print("Run is not counted")
                    print("Try again")
                    continue
                z=random.randrange(0,7)
                print("The number entered by the computer is:",z)
                if sum1>=200:
                    print("Maximum runs taken")
                    break
                elif q==z:
                    print("--Out--")
                    w1-=1
                    if w1>0:
                        print("--Next wicket starting--")
                else:
                    sum1+=q
                    if sum1>sum3:
                        break
            except KeyboardInterrupt:
                print("---Game ended---")
                sys.exit()
            except ValueError:
                print("Enter number only\nTry again")
            except Exception as err:
                print("An error has occurred:",err)

        print("Total runs",sum1)
        res(sum1,sum3)

    start(k1,k7)

try:
    print("To end the game in the middle press Ctrl+C")
    m3=input("Enter username: ").strip()

    if not m3:
        print("Invalid username")
        sys.exit()

    if len(m3)>250:
        print("Username must contain 250 characters or less")
        sys.exit()

    m2=input("Enter password of your mysql: ")
    database()

except KeyboardInterrupt:
    print("---Game ended---")