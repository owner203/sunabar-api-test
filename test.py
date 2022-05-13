import http.client
import json

class sunabar_api:
    def conn_initialize():
        return http.client.HTTPSConnection("api.sunabar.gmo-aozora.com") #ここにAPI URIを入れる

    def headers_initialize():
        headers = {
            'Accept': "application/json;charset=UTF-8",
            'Content-Type': "application/json",
            'x-access-token': ""
        }
        headers['x-access-token'] = "ここにトークンを入れる" #ここにトークンを入れる
    
        return headers

    def get_accounts_info():
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize()
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

        return [mainAccountId, appAccountId]

    def get_balances(accountId):
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize()
        conn.request("GET", "/personal/v1/accounts/balances?accountId=" + accountId, headers=headers)

        res = conn.getresponse()
        data = res.read()

        #print(data.decode("utf-8"))
        data_json = json.loads(data.decode("utf-8"))
        #print(json.dumps(data_json, ensure_ascii=False, indent=2))

        return data_json.get('spAccountBalances')[0].get('odBalance')

    def transfer_saving(debitSpAccountId, depositSpAccountId, paymentAmount): #親口座 → 貯金星
        conn = sunabar_api.conn_initialize()
        headers = sunabar_api.headers_initialize()

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
        #print(data_str)

        data_json = json.loads(data_str)
        #print(json.dumps(data_json, ensure_ascii=False, indent=2))

        return [data_json.get('paymentAmount'), data_json.get('errorMessage')]

class game_action:
    def show_spAccount_not_found_message():
        print("先につかいわけ口座を作成してください https://bank.sunabar.gmo-aozora.com/bank/sp-account")
        print("1 = もう一度試す")
        print("0 = ゲーム終了")
        print("アクションを選択してください：\n>> ", end='')

        return 0

    def game_initialize():
        if not sunabar_api.get_accounts_info()[1]:
            actionSelect = ""
            while not actionSelect:
                game_action.show_spAccount_not_found_message()
                actionSelect = input()

            match actionSelect:
                case "1":
                    return 1
                case "0":
                    print("さようなら！\n")
                    exit(0) 

        return 0

    def show_main_menu():
        print("メインメニューです：")
        print("1 = 口座残高確認")
        print("2 = アイテム購入")
        print("0 = ゲーム終了")
        print("アクションを選択してください：\n>> ", end='')

        return 0

    def show_balances():
        accountsInfo = sunabar_api.get_accounts_info()
        mainAccountId = accountsInfo[0] #親口座
        appAccountId = accountsInfo[1] #貯金星

        print("現在の親口座残高は" + sunabar_api.get_balances(mainAccountId) + "円です。\n現在の貯金星残高は" + sunabar_api.get_balances(appAccountId) + "円です。\n")
    
        return 0

    def show_item_list():
        print("メニューはこちらです：")
        print("1 = 🍎50円")
        print("2 = 🍌100円")
        print("3 = 🍐500円")
        print("4 = 🚗50000円")
        print("0 = キャンセル")
        print("購入するアイテムを選択してください：\n>> ", end='')

        return 0

    def item_purchase():
        accountsInfo = sunabar_api.get_accounts_info()
        mainAccountId = accountsInfo[0] #親口座
        appAccountId = accountsInfo[1] #貯金星
        
        itemSelect = ""
        while not itemSelect:
            game_action.show_item_list()
            itemSelect = input()

        match itemSelect:
            case "1":
                paymentAmount = 50
            case "2":
                paymentAmount = 100
            case "3":
                paymentAmount = 500
            case "4":
                paymentAmount = 50000
            case "0":
                paymentAmount = 0
                print("キャンセルされました！\n")
                return 0
        
        return_status = sunabar_api.transfer_saving(mainAccountId, appAccountId, str(paymentAmount))
        if return_status[0] == str(paymentAmount):
            print("購入しました！\n")
        else: 
            print(return_status[1])
        
        return 0

    def main_menu_select():
        game_action.show_main_menu()
        actionSelect = input()
        match actionSelect:
            case "1":
                game_action.show_balances()
            case "2":
                game_action.item_purchase()
            case "0":
                print("さようなら！\n")
                return 1
        
        return 0
    
    def run_game():
        while game_action.game_initialize() != 0:
            continue

        while game_action.main_menu_select() == 0:
            continue
        
        return 0

if __name__ == '__main__':
    game_action.run_game()
