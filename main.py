import os, re, webbrowser
import tkinter
from tkinter import dialog, filedialog, Label
from tkinter.constants import CENTER, DISABLED, END, GROOVE, NORMAL, X
from tkinter.scrolledtext import ScrolledText
import tkinter.messagebox

class LinkLabel(Label):  # 超链接
    def __init__(self,master,link,font=('微软雅黑',10),bg='#f0f0f0'):
        super().__init__(master,text=link,font=font,fg='blue',bg=bg)
        self.link = 'https://github.com/zzpong/Clanbattle-Timeline-Modifier/issues'
        self.bind('<Enter>',self._changecolor)
        self.bind('<Leave>',self._changecurcor)
        self.bind('<Button-1>',self._golink)
        self.isclick=False  # 未被点击
    
    def _changecolor(self, event):
        self['fg'] = '#D52BC4'  # 鼠标进入，变为紫色
        self['cursor'] = 'hand2'
    
    def _changecurcor(self, event):
        if self.isclick == False:  # 如果链接未被点击，显示为蓝色
            self['fg'] = 'blue'
        self['cursor'] = 'xterm'
    
    def _golink(self,event):
        self.isclick = True  # 被链接点击后不再改变颜色
        webbrowser.open(self.link)

class ScrolledTextRightClick:
    def __init__(self, scrolledTextHandle):
        self.scrolledTextHandle = scrolledTextHandle
    def onPaste(self):
        try:
            self.text = self.scrolledTextHandle.clipboard_get()
            # result = self.scrolledTextHandle.selection_get(selection="CLIPBOARD")
        except tkinter.TclError:
            pass
        self.scrolledTextHandle.insert('insert', str(self.text))
    def onCopy(self):
        self.scrolledTextHandle.clipboard_clear()
        self.text = self.scrolledTextHandle.get('1.0', END)
        self.scrolledTextHandle.clipboard_append(self.text)
        pass
    def onCut(self):
        self.onCopy()
        try:
            self.scrolledTextHandle.delete('1.0', END)
        except tkinter.TclError:
            pass


def sendMessage(message:str):
    textOutput.config(state=NORMAL)
    textOutput.delete('1.0', END)
    textOutput.insert('insert', message)
    textOutput.config(state=DISABLED)
    return

def sendError(message:str):
    tkinter.messagebox.showerror('错误',message)

def getTailTime(message:str) -> str:
    matchObj = re.search(r'(\d{1})[:：](\d{2})', message, re.M|re.I)
    if matchObj is not None:
        realTime = int(matchObj.group(1))*60 + int(matchObj.group(2))
        print(realTime)
        print(matchObj.group(1)+matchObj.group(2))
        return realTime
    else:
        sendError('请输入正确格式尾刀时间，如“1:26”')
        return

def processTime(message:str, tailTime:int) -> str:
    matchObj1 = re.search(r'(\d{1})[:：]*(\d{2})', message, re.M|re.I)  # 1:25, 125, 0:27, 027 (其实也可以删除":"提前normalize一下)
    matchObj2 = re.search(r'[:：]*(\d{2})', message, re.M|re.I)  # 57
    matchObj3 = re.search(r'[:：]*(\d{1})', message, re.M|re.I)  # 3
    if matchObj1 is not None:
        realTime = int(matchObj1.group(1))*60 + int(matchObj1.group(2)) - (90 - tailTime)
    elif matchObj2 is not None:
        realTime = int(matchObj2.group(1)) - (90 - tailTime)
    elif matchObj3 is not None:
        realTime = int(matchObj3.group(1)) - (90 - tailTime)
    if realTime is not None:
        if realTime >= 60:
            realTimeStr = "1:" + str(realTime-60).zfill(2)
            return realTimeStr
        elif realTime >=0:
            realTimeStr = "0:" + str(realTime).zfill(2)
            return realTimeStr
        else:
            return 'NoNeed'
    else:
        sendError('请使用正确时间轴格式')
        return

def processOneLine(message:str, tailTime:int) -> list:
    # matchObj = re.match(r'(.*)\s(.*)', message)
    matchObj = re.match(r'(\d*[:：]*\d+)\s?(.*)', message)  # 此处支持":45"格式, 但后面计算真实时间并未使用
    if matchObj is not None:
        curTime = matchObj.group(1)
        realTime = processTime(curTime, tailTime)
        txt = matchObj.group(2)
        print(curTime)
        return [realTime, txt]
    else:
        return [message]

def modify():
    tailTime = getTailTime(entry.get())
    timeLine = textInput.get('1.0', END)
    timeLineList = re.split('\n', timeLine)
    print(timeLineList)
    modifiedTL = ""
    for tl in timeLineList:
        oneLine = processOneLine(tl, tailTime)
        if len(oneLine) > 1 and oneLine[0] != 'NoNeed':
            modifiedTL = modifiedTL + f"{oneLine[0]} {oneLine[1]}\n"
        elif len(oneLine) > 1 and oneLine[0] == 'NoNeed':
            break
        else:
            modifiedTL = modifiedTL + f"{oneLine[0]}\n"
        # modifiedTL.append(processOneLine(tl, tailTime))
    # 这儿简洁版可用map函数
    sendMessage(modifiedTL)
    return

def clearInput():
    textInput.delete('1.0', END)
    return

def save():
    global file_path
    global file_text
    file_path = filedialog.asksaveasfilename(title=u'保存文件', initialfile=u'时间轴.txt', filetypes=[('文本文档', '.txt'), ('All Files', '*')])  # initialfile是为文件自动后缀存在的
    print('保存文件：', file_path)
    file_text = textOutput.get('1.0', END)
    if file_path is not None:
        with open(file=file_path, mode='a+', encoding='utf-8') as file:
            file.seek(0)
            file.truncate()  # 先清空
            file.write(file_text)
            dialog.Dialog(None, {'title': 'File Modified', 'text': '保存完成', 'bitmap': 'warning', 'default': 0,
                    'strings': ('OK', 'Cancel')})
            print('保存完成')
    return


# 主窗口
mainWin = tkinter.Tk()
mainWin.title('补偿刀时间轴修正工具')
mainWin.geometry('1000x700')

# ## 输入窗口, 这类输入窗parents是textbox会导致文本不显示 (仅y滑块), 或者只显示极小部分 (设置两个滑块)
# textInput = tkinter.Text(mainWin, width=500, height=400)
# # scrollInputX = tkinter.Scrollbar(textInput, orient=HORIZONTAL, command=textInput.xview)
# # scrollInputX = tkinter.Scrollbar(textInput)
# # scrollInputX.pack(side=tkinter.BOTTOM, fill=tkinter.X)
# scrollInputY = tkinter.Scrollbar(textInput)
# scrollInputY.pack(side=tkinter.RIGHT, fill=tkinter.Y)
# # 控件关联
# # scrollInputX.config(orient=HORIZONTAL, command=textInput.xview)
# # textInput.config(xscrollcommand=scrollInputX.set)
# scrollInputY.config(command=textInput.yview)
# textInput.config(yscrollcommand=scrollInputY.set)

# # textInput.pack(side='left', expand='yes', anchor='w', fill='none', padx=5, pady=5)

# 输入窗口
textInput = ScrolledText(mainWin, width=50, height=400)
textInput.pack(side='left', expand='yes', anchor='w', fill='both', padx=5, pady=5)

# 输出窗口
textOutput = ScrolledText(mainWin, width=50, height=400, state=DISABLED)  # 禁止写入
textOutput.pack(side='right', expand='yes', anchor='e', fill='both', padx=5, pady=5)

# 相关按键
frame = tkinter.Frame(mainWin, relief=GROOVE)
frame.pack(expand='yes', anchor='center', fill='x', padx=5, pady=5)

link = LinkLabel(frame, link='反馈BUG').pack(pady=10)

tkinter.Label(frame, text='<= 在此填轴     输出结果 =>').pack(pady=50)

tkinter.Label(frame, text='请输入补偿时间').pack()

entry = tkinter.Entry(frame, justify=CENTER)
entry.pack(pady=10)
entry.delete(0, END)
entry.insert(0,'1:26')

path = os.path.abspath('.')
imgBtn1 = tkinter.PhotoImage(file=os.path.join(path, 'suzuna.png'))
btn1 = tkinter.Button(frame, image=imgBtn1, text='修正', width=15, compound=tkinter.TOP, command=modify)
btn1.pack(fill=X, pady=1)

btn2 = tkinter.Button(frame, text='导出', width=15, command=save)
btn2.pack(fill=X)

btn2 = tkinter.Button(frame, text='清空', command=clearInput)
btn2.pack(fill=X)

textInput.pack()

# textInput右键弹窗
def cut(event=None):
    textInput.event_generate("<<Cut>>")
def copy(event=None):
    textInput.event_generate("<<Copy>>")
def paste(event=None):
    textInput.event_generate('<<Paste>>')

menu = tkinter.Menu(textInput, tearoff=0)
menu.add_command(label="复制", command=copy)
menu.add_separator()
menu.add_command(label="粘贴", command=paste)
menu.add_separator()
menu.add_command(label="剪切", command=cut)

def popupmenu(event):
    menu.post(event.x_root, event.y_root)
textInput.bind("<Button-3>", popupmenu)

# textOutput右键弹窗
def copyOut(event=None):
    textOutput.event_generate("<<Copy>>")

menuOut = tkinter.Menu(textOutput, tearoff=0)
menuOut.add_command(label="复制", command=copyOut)

def popupmenuOut(event):
    menuOut.post(event.x_root, event.y_root)
textOutput.bind("<Button-3>", popupmenuOut)


mainWin.mainloop()