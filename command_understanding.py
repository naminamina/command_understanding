#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import openai
import datetime

#ChatGptの利用にはOpenAiのapikeyが必要
#環境変数でOPENAI_API_KEYを入力
openai.api_key = os.getenv("OPENAI_API_KEY")
#OPENAI_API_KEYを直接入力
# openai.api_key = ""



# テスト用サンプル
object = "cup"
placement = "long table"
room = "living room"
name = "taro"
beacon = "room"
sample = [
    "go to the living room look for jack tell your teams name",
    "get the orange and take it to banana"

]


#タスクとタスクに必要な変数の辞書
VALUE_NOUN = {

    "Navigation_navigate":["PERSON" ,"TARGET_PLACE"],
    "Navigation_Chace":["MOVE_PLACE","TARGET_PERSON"],
    "Speech_Ask":["ASK"],
    "Speak":["GESTURE"],
    "Speech_Answer":["GESTURE"],
    "Carrying": ["MOVE_PLACE", "CARRYING_OBJECT","TARGET_PLACE","TARGET_PERSON"],
    "Vision": ["MOVE_PLACE","TARGET_PERSON"],
}

#タスクとそれに分類される動詞の辞書
KEY_VERB = {
    "Navigation_navigate":["guide"],
    "Navigation_Chace":["follow"],
    "Speech_Answer":["answer"],
    "Speak":["tell","say","speak"],
    "Speech_Ask":["ask"],
    "Carrying":  ["bring","carry","deliver","take","place_on","give"],
    "Vision":["find","look_for"],


}

#タスクと変数の辞書2
VALUE_NOUN_2 = {
    "Carrying": ["MOVE_PLACE", "TARGET_PLACE","CARRYING_OBJECT","TARGET_PERSON"],
    "Vision": ["MOVE_PLACE","TARGET"],
    "Navigation_Chace":["MOVE_PLACE","TARGET_PERSON"],
    "Navigation_navigate":["MOVE_PLACE","TARGET_PLACE","TARGET_PERSON"],
    "Speak":["MOVE_PLACE","TARGET","GESTURE"],
    "Speech_Answer":["MOVE_PLACE","TARGET","GESTURE"], #Speech_AnswerにGESTUREは必要ないが出力を安定させるため
    "Speech_Ask":["MOVE_PLACE","TARGET","ASK"]

}

#KEYの包括関係
INCLUSION_RELATION = {                                         
    "Vision" :["Navigation_navigate","Carrying"],
    "Speech_Answer":["Vision","Navigation_navigate","Carrying"],
    "Speech_Ask":["Vision","Navigation_navigate","Carrying"],
    "Speak":["Vision","Navigation_navigate","Carrying"],
    "Navigation_Chace":["Vision","Navigation_navigate","Carrying","Speak","Speech_Ask","Speech_Answer"]
} 



date = datetime.datetime.now()
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
QUESTIONS = {
                    "the name of your team":"Our team's name is KIT HAPPY ROBOT",
                    "your name":"I am Happy Mimi",
                    "your team's country":"Our team's country is Japan",
                    "What day is today": date.strftime("%B%d"),
                    "What day is tomorrow":tomorrow.strftime("%B%d"),
                    "tell the day of the month":date.strftime('%B'),
                    "tell the day of the week":date.strftime('%A'),
                    "tell the date":date.strftime("%B%d"),
                    "what time is it":date.strftime("%H%M"),
                    "the time":date.strftime("%H%M"),
}
NAMES = {}
POSTURES = {}
PREDEFINED_LOCATION = {}


class UseGpts:
    def __init__(self):
        self.system_message = "You are Api.Resopnse JSON format on the following context."
        self.model = "gpt-4-turbo-preview"
    
    def returnJson(self, prompt):
        response = openai.ChatCompletion.create(
            model = self.model,
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
                ],
                response_format={ 'type': 'json_object' },#必ずJSONで返してくれるようになる
                temperature=0,
        )

        return response['choices'][0]['message']['content']



class MakePrompt:
    def __init__(self, user_message):
        self.user_message = user_message
        self.key_dictionary = KEY_VERB
        self.value_dictionary = VALUE_NOUN
        self.value_dictionary_2 = VALUE_NOUN_2
        self.relation_dictionary = INCLUSION_RELATION

        # gpsr_infomation_json = open('./gpsr_infomation.json', 'r')
        
        # self.question_dictionary = QUESTIONS
        # self.question_dictionary.update(json.load(gpsr_infomation_json)["questions"][0])

        # self.names_dictionary = json.load(gpsr_infomation_json)["names"][0]
        # self.postures_dictionary = json.load(self.gpsr_infomation_json)["postures"]
        # self.objects_dictionary = json.load(self.gpsr_infomation_json)["objects"]
        # print(self.names_dictionary)
        # print(self.question_dictionary)
        # print(self.postures_dictionary)
        # print(self.objects_dictionary)


    def FirstPrompt(self):
        key_prompt = ""
        value_prompt = "動詞goto,navigation to,reach,get intoに続くPLACEはVALUE:MOVE_PLACEの値になる。 "
        #辞書型を展開して文字列にしてGPTに入力
        for j in self.key_dictionary.keys():
            key_prompt +=  "動詞"
            for i in range(len(self.key_dictionary[str(j)])):
                key_prompt +=  self.key_dictionary[str(j)][i]  + ","
            key_prompt += " はKey:" + str(j) + "に分類される。"

        for j in self.value_dictionary.keys():
            value_prompt +=  "KEY:" + str(j) +"は " 
            for i in range(len(self.value_dictionary[str(j)])):
                value_prompt +=  self.value_dictionary[str(j)][i]  + ","    
            value_prompt += "のVALUEを必ずもつ。VALUEに対応する値を必ず入れなさい。trueなどは入力してはならないVALUEに対応する値が存在しない場合はのみfalseにしなさい 。"


        #もっと改良できるはず
        #存在しないときはvalueにFalseが入力される
        return f"命令文章を解析し、ロボットがすべき行動と目標物、移動場所とともに必ず2次元のJSON型データにして出力してください。\
            またKEYの順番は  ロボットがすべき行動に基づいてロボットがすべき行動を時系列順にしなさい \
            JSONデータのKEYは、{key_prompt}という規則にしたがって設定してください。\
            JSONデータのVALUEは {value_prompt} という規則に従がって必ず設定ください。\
            またVALUEであるQUESTION,ASKの値には、VALUE名に対応した名詞節を入れなさい。\
            しかし前述までの処理でロボットがすべき行動が達成できない と判断した場合は、規則に従いKEYとVALUEを設定しても良い。\
            必ず2次元のJSON型で返答してください。 \
            返答には日本語などJSON型以外の文章は一切含まないでください。命令文章:{self.user_message}"


    def SecondPrompt(self, result):
        key_prompt = ""
        value_prompt = "動詞goto,navigation to,reach,get intoに続くPLACEはVALUE:MOVE_PLACEの値になる。 "
        relation_prompt = ""
        #辞書型を展開して文字列にしてGPTに入力
        for j in self.key_dictionary.keys():
            key_prompt +=  "動詞"
            for i in range(len(self.key_dictionary[str(j)])):
                key_prompt +=  self.key_dictionary[str(j)][i]  + ","
            key_prompt += " はKey:" + str(j) + "に分類される。"

        for j in self.value_dictionary_2.keys():
            value_prompt +=  "KEY:" + str(j) +"は " 
            for i in range(len(self.value_dictionary_2[str(j)])):
                value_prompt +=  self.value_dictionary_2[str(j)][i]  + ","    
            value_prompt += "のVALUEを必ずもつ。VALUEに対応する値を命令文章から推測し、必ず入力しなさい。"

        for j in self.relation_dictionary.keys():
            relation_prompt += "命令文章が" + str(j) + ","
            for i in range(len(self.relation_dictionary[str(j)])):
                relation_prompt += self.relation_dictionary[str(j)][i] + ","
            relation_prompt += "のうち2つ以上をKEYとしてもつ場合" + str(j) + "をKEYにしなさい ."
        #もっと改良できるはず
        #存在しないときはvalueにFalseが入力される
        return f"命令文章を解析し、ロボットがすべき行動と目標物、移動場所とともに必ず2次元のJSON型データにして出力してください。\
            命令文章が2つ以上のKEYをもつJSON型データの場合、\
            JSON型のVALUEは{result}のVALUEの値と命令文章から推測し、違うKEYに同じVALUEが存在する場合は命令文章から推測して、ロボットがすべき行動と目標物、移動場所としてふさわしい値を必ず入力しなさい。\
            命令文章が2つ以上のKEYをもつJSON型データの場合、\
            {relation_prompt}という規則に従いKEYを必ず1つだけ選んで、ロボットがすべき行動の目標物、移動場所とともに必ず2次元のJSON型データにして出力してください。\
            KEYが複数ある場合は間違いなので推論をやり直しなさい。\
            JSONデータのVALUEは {value_prompt}という規則に従がって入力しなさい。\
            命令文章:{self.user_message}"
    
    def FirstCategory3Prompt(self):
        key_prompt = ""
        value_prompt = "動詞goto,navigation to,reach,get intoに続くPLACEはVALUE:MOVE_PLACEの値になる。 "
        relation_prompt = ""
        #辞書型を展開して文字列にしてGPTに入力
        for j in self.key_dictionary.keys():
            key_prompt +=  "動詞"
            for i in range(len(self.key_dictionary[str(j)])):
                key_prompt +=  self.key_dictionary[str(j)][i]  + ","
            key_prompt += " はKey:" + str(j) + "に分類される。"

        for j in self.value_dictionary_2.keys():
            value_prompt +=  "KEY:" + str(j) +"は " 
            for i in range(len(self.value_dictionary_2[str(j)])):
                value_prompt +=  self.value_dictionary_2[str(j)][i]  + ","    
            value_prompt += "のVALUEを必ずもつ。"

        for j in self.relation_dictionary.keys():
            relation_prompt += "命令文章が" + str(j) + ","
            for i in range(len(self.relation_dictionary[str(j)])):
                relation_prompt += self.relation_dictionary[str(j)][i] + ","
            relation_prompt += "のうち2つ以上をKEYとしてもつ場合" + str(j) + "をKEYにしなさい ."
        #もっと改良できるはず
        #存在しないときはvalueにFalseが入力される
        return f"次の命令文章は、場所や人、物の名前の不足情報、誤情報が含まれいている。\
            命令文章中の人や物が存在しない可能性がある。\
            既知情報として人はMEしかいない、物体は,bananaとcrackersしかないことが分かっている。またcrackersがbedにおいてある可能性があり、bananaがbathroomロッカーに置いてある可能性があることを考慮して不足情報、誤情報をもっとも可能性がある値で補完しなさい。\
            不足情報、誤情報には本来人の名前が入るべき動詞の後に物の名前が、本来物の名前が入るべき動詞のあとに人物名が入るものなどがある。\
            不足情報、誤情報が含まれいていことを考慮しロボットがすべき行動と目標物、移動場所とともに必ず2次元のJSON型データにして出力してください。\
            命令文章の不足情報、誤情報を次の規則に従い補完しなさい。\
            またKEYの順番は  ロボットがすべき行動に基づいてロボットがすべき行動を時系列順にしなさい \
            JSONデータのKEYは、{key_prompt}という規則にしたがって設定してください。\
            JSONデータのVALUEは {value_prompt} という規則に従がって必ず設定ください。\
            またVALUEであるQUESTION,ASKの値には、VALUE名に対応した名詞節を入れなさい。\
            しかし前述までの処理でロボットがすべき行動が達成できない と判断した場合は、規則に従いKEYとVALUEを設定しても良い。\
            必ず2次元のJSON型で返答してください。 \
            返答には日本語などJSON型以外の文章は一切含まないでください。命令文章:{self.user_message}"

def commnad_understanding(user_message):
    print(user_message)
    prompt = MakePrompt(user_message)
    # print(prompt.returnPrompt())
    result = UseGpts().returnJson(prompt.FirstPrompt())
    # print(result)
    second_prompt = prompt.SecondPrompt(result)
    # print(second_prompt)
    result = UseGpts().returnJson(second_prompt)
    # print(result)
    return result


def command_understanding_category3(user_message):
    print(user_message)
    prompt = MakePrompt(user_message)
    # print(prompt.returnPrompt())
    result = UseGpts().returnJson(prompt.FirstCategory3Prompt())
    # # print(result)
    # second_prompt = prompt.SecondPrompt(result)
    # # print(second_prompt)
    # result = UseGpts().returnJson(second_prompt)
    # print(result)
    return result




def main(message):
    rospy.init_node('return_command_json')
    result = rospy.Service('command_understanding', happymimi_msgs, command_understanding)
    rospy.spin()
    return result



if __name__ == '__main__':
    print(commnad_understanding("go to the living room look for jack tell your teams name"))

 


