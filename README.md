# 述

工作的时候，要求要找不同地方的同一性质的资产，为了避免麻烦，所以干脆找ai写了一个脚本，感觉蛮好用的，想着以后若是更新或者增加功能点，方便回想功能的构造，所用api为hunter的，在此记录如下

## 原理

全组合-笛卡尔积

| all-body | domain | all-title | \|body | title! |
| -------- | ------ | --------- | ------ | ------ |
| 河南     | pay    | 读书      | a      | 湖北   |
| 郑州     | go     | 支付      | b      |        |
| 开封     |        |           |        |        |



all-"标题"一行会与"标题"一列全组合

!代表减去对应的标题；如：web.title!=""

|代表括号中的或语句；如：(web.title="" || web.title="")

使用方法python search2.py -l  你的文档.xlsx

1. **组合1**
   `body="河南" && title="读书" && domain="pay" && domain="go" && (body="a"||body="b")` && title != "湖北"
   （`all-body`取"河南" + `all-title`取"读书" + 普通列`domain`取"pay"和"go" + OR列`body`取"a"或"b" + !取"湖北"）
2. **组合2**
   `body="河南" && title="支付" && domain="pay" && domain="go" && (body="a"||body="b") && title!= "湖北"`
   （`all-body`取"河南" + `all-title`取"支付" + 其他条件同上）
3. **组合3**
   `body="郑州" && title="读书" && domain="pay" && domain="go" && (body="a"||body="b") && title!= "湖北"`
4. **组合4**
   `body="郑州" && title="支付" && domain="pay" && domain="go" && (body="a"||body="b") && title!= "湖北"`
5. **组合5**
   `body="开封" && title="读书" && domain="pay" && domain="go" && (body="a"||body="b") && title!= "湖北"`
6. **组合6**
   `body="开封" && title="支付" && domain="pay" && domain="go" && (body="a"||body="b") && title!= "湖北"`

## 注意：标题下面必须存在内容

​	    需要填入自己的hunter的api	//第190行处

### 工作流程

"""生成所有搜索组合"""

"""构造搜索查询语句并编码"""

"""发送API请求"""

"""处理API返回结果"""

"""保存为Excel文件"""


