## 一个mac版的人脸识别锁屏python脚本

当您离开电脑时，几秒后通过人脸识别技术，识别出您不在了，电脑自动锁屏；
当前电脑面前不是您在操作，也会自动锁屏；并拍照记录当前是谁。
确保当前电脑以联网。

### 注意：
* python3版本
### 使用步骤
* pip3 install -r requirements.txt 安装所需包
* 到[http://ai.baidu.com/tech/face] 百度人脸识别官网免费注册获得API_key 和access_key填到conf.ini文件相应位置
* 将picture文件夹的myFace.jpg文件替换成你的自拍
* python3 face_lock.py开始运行
