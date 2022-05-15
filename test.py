import http.client
import json
import sqlite3

class sunabar_api:
    def conn_initialize():
        apiDomainName = "api.sunabar.gmo-aozora.com"

        return http.client.HTTPSConnection(apiDomainName)

    def headers_initialize(accessToken):
        headers = {
            'Accept': "application/json;charset=UTF-8",
            'Content-Type': "application/json",
            'x-access-token': ""
        }
        headers['x-access-token'] = accessToken
    
        return headers

    def get_accounts_info(accessToken):
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize(accessToken)
        conn.request("GET", "/personal/v1/accounts", headers=headers)

        res = conn.getresponse()
        data = res.read()

        #print(data.decode("utf-8"))
        data_json = json.loads(data.decode("utf-8"))
        #print(json.dumps(data_json, ensure_ascii=False, indent=2))

        if len(data_json.get('spAccounts')) == 1:
            mainAccountId = data_json.get('spAccounts')[0].get('accountId')
            appAccountId = ""
        else:
            mainAccountId = data_json.get('spAccounts')[0].get('accountId')
            appAccountId = data_json.get('spAccounts')[1].get('accountId')

        res.close()
        conn.close()

        return (mainAccountId, appAccountId)

    def get_balances(accessToken, accountId):
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize(accessToken)
        conn.request("GET", "/personal/v1/accounts/balances?accountId=" + accountId, headers=headers)

        res = conn.getresponse()
        data = res.read()

        #print(data.decode("utf-8"))
        data_json = json.loads(data.decode("utf-8"))
        #print(json.dumps(data_json, ensure_ascii=False, indent=2))

        res.close()
        conn.close()
        
        return data_json.get('spAccountBalances')[0].get('odBalance')

    def transfer_saving(accessToken, debitSpAccountId, depositSpAccountId, paymentAmount):
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize(accessToken)

        payload = "{\n  \"depositSpAccountId\": \"__depositSpAccountId__\",\n  \"debitSpAccountId\": \"__debitSpAccountId__\",\n  \"currencyCode\": \"JPY\",\n  \"paymentAmount\": \"__paymentAmount__\"\n}"
        payload = payload.replace('__debitSpAccountId__', debitSpAccountId)
        payload = payload.replace('__depositSpAccountId__', depositSpAccountId)
        payload = payload.replace('__paymentAmount__', str(paymentAmount))

        conn.request("POST", "/personal/v1/transfer/spaccounts-transfer", payload, headers)

        res = conn.getresponse()
        data = res.read()

        #print(data.decode("utf-8"))
        data_str = str(data.decode("utf-8"))
        data_str = data_str.replace('\"currencyName\"', ',\"currencyName\"')
        #返り値のデータに、「"currencyName"」の直前のところで「,」が一個抜けてる、というバグがあるので、対応する

        data_json = json.loads(data_str)
        #print(json.dumps(data_json, ensure_ascii=False, indent=2))

        res.close()
        conn.close()
        
        return [data_json.get('paymentAmount'), data_json.get('errorMessage')]

class db_action:
    def conn_initialize():
        dbname = "chokinsei_db.sqlite3"

        return sqlite3.connect(dbname)
    
    def db_reset():
        #データベースをリセットする
        #デバッグ用途のみ
        def show_message():
            print("確定しますか？(y/n)\n>> ", end='')

            return 0

        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('DROP TABLE player_data')
        cur.execute('CREATE TABLE player_data(id INTEGER PRIMARY KEY AUTOINCREMENT, key STRING, value STRING)')
        
        tokenSet = 'INSERT INTO player_data(key, value) values(\"access_token\", \"__accessToken__\")'
        
        accessToken = ""
        while not accessToken:
            print("トークンを入力してください：\n>> ", end='')
            accessToken = input()
            
            actionSelect = ""
            while not actionSelect:
                show_message()
                actionSelect = input()

                match actionSelect:
                    case "y":
                        break
                    case "n":
                        accessToken = ""
                    case _:
                        actionSelect = ""
            
        tokenSet = tokenSet.replace('__accessToken__', accessToken)
        
        cur.execute(tokenSet)
        cur.execute('INSERT INTO player_data(key, value) values(\"main_account_id\", \"\")')
        cur.execute('INSERT INTO player_data(key, value) values(\"app_account_id\", \"\")')
        cur.execute('INSERT INTO player_data(key, value) values(\"last_balance\", \"\")')
        cur.execute('INSERT INTO player_data(key, value) values(\"last_login\", \"\")')
        cur.execute('INSERT INTO player_data(key, value) values(\"goal_value\", \"\")')
        
        conn.commit()

        cur.close()
        conn.close()
        
        return 0

    def get_token():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="access_token"')
        data = cur.fetchall()

        cur.close()
        conn.close()
        
        return data[0][0]

    def get_main_account_id():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="main_account_id"')
        data = cur.fetchall()

        cur.close()
        conn.close()
        
        return data[0][0]

    def get_app_account_id():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="app_account_id"')
        data = cur.fetchall()

        cur.close()
        conn.close()
        
        return data[0][0]

    def get_last_balance():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="last_balance"')
        data = cur.fetchall()

        cur.close()
        conn.close()
            
        return data[0][0]
    
    def get_last_login():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="last_login"')
        data = cur.fetchall()

        cur.close()
        conn.close()
            
        return data[0][0]

    def get_goal_value():
        conn = db_action.conn_initialize()
        cur = conn.cursor()

        cur.execute('SELECT value FROM player_data WHERE key="goal_value"')
        data = cur.fetchall()

        cur.close()
        conn.close()
            
        return data[0][0]

class game_action:
    def show_accessToken_not_found_message():
        print("トークンが見つかりませんでした")
        print("1 = もう一度試す")
        print("0 = ゲーム終了")
        print("アクションを選択してください：\n>> ", end='')

    def show_spAccount_not_found_message():
        print("先につかいわけ口座を作成してください https://bank.sunabar.gmo-aozora.com/bank/sp-account")
        print("1 = もう一度試す")
        print("0 = ゲーム終了")
        print("アクションを選択してください：\n>> ", end='')

        return 0

    def token_status_check():
        while not db_action.get_token():
            actionSelect = ""
            while not actionSelect:
                game_action.show_accessToken_not_found_message()
                actionSelect = input()

                match actionSelect:
                    case "1":
                        break
                    case "0":
                        print("さようなら！\n")
                        exit(0)
                    case _:
                        actionSelect = ""

        return 0
    
    def spAccount_status_check():
        while not sunabar_api.get_accounts_info(db_action.get_token())[1]:
            actionSelect = ""
            while not actionSelect:
                game_action.show_spAccount_not_found_message()
                actionSelect = input()

                match actionSelect:
                    case "1":
                        break
                    case "0":
                        print("さようなら！\n")
                        exit(0)
                    case _:
                        actionSelect = ""
        
        return 0

    def game_initialize():
        game_action.token_status_check()
        game_action.spAccount_status_check()

        return 0

    def show_main_menu():
        print("メインメニューです：")
        print("1 = 口座残高確認")
        print("2 = アイテム購入")
        print("0 = ゲーム終了")
        print("アクションを選択してください：\n>> ", end='')

        return 0

    def show_balances():
        accountsInfo = sunabar_api.get_accounts_info(db_action.get_token())
        mainAccountId = accountsInfo[0] #親口座
        appAccountId = accountsInfo[1] #貯金星

        print("現在の親口座残高は" + sunabar_api.get_balances(db_action.get_token(), mainAccountId) + "円です。\n現在の貯金星残高は" + sunabar_api.get_balances(db_action.get_token(), appAccountId) + "円です。\n")
    
        return 0

    def show_item_list():
        print("メニューはこちらです：")
        print("1 = 🍎50円")
        print("2 = 🍌100円")
        print("3 = 🍐500円")
        print("4 = 🚗999999円")
        print("0 = キャンセル")
        print("購入するアイテムを選択してください：\n>> ", end='')

        return 0

    def item_purchase():
        accountsInfo = sunabar_api.get_accounts_info(db_action.get_token())
        mainAccountId = accountsInfo[0] #親口座
        appAccountId = accountsInfo[1] #貯金星
        
        itemSelect = ""
        while not itemSelect:
            game_action.show_item_list()
            itemSelect = input()

            match itemSelect:
                case "1":
                    paymentAmount = 50
                    break
                case "2":
                    paymentAmount = 100
                    break
                case "3":
                    paymentAmount = 500
                    break
                case "4":
                    paymentAmount = 999999
                    break
                case "0":
                    paymentAmount = 0
                    print("キャンセルされました！\n")
                    return 0
                case _:
                    itemSelect = ""

        return_status = sunabar_api.transfer_saving(db_action.get_token(), mainAccountId, appAccountId, str(paymentAmount))
        if return_status[0] == str(paymentAmount):
            print("購入しました！\n")
        else: 
            print(return_status[1])
        
        return 0

    def main_menu_select():
        actionSelect = ""
        while not actionSelect:
            game_action.show_main_menu()
            actionSelect = input()
        
            match actionSelect:
                case "1":
                    game_action.show_balances()
                    actionSelect = ""
                case "2":
                    game_action.item_purchase()
                    actionSelect = ""
                case "0":
                    print("さようなら！\n")
                    exit(0)
                case _:
                    actionSelect = ""
        
        return 0
    
    def run_game():
        #db_action.db_reset() #デバッグ用途のみ
        game_action.game_initialize()
        game_action.main_menu_select()
        
        return 0

if __name__ == '__main__':
    game_action.run_game()
