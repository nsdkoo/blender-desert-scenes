# Qasr al-Raml · 沙垒：最后的琥珀光

原创的中世纪沙漠城堡攻防战静帧场景，完全由 Blender Python 程序化构建。所有几何与材质均在本地生成，无外部模型、图片纹理或品牌元素。

![Qasr al-Raml](./preview_hd.png)

## 场景内容

双塔拱门、石砌城墙、城垛、箭塔、局部坍塌缺口、向内打开的木门、庭院、石阶和木棚。城外含沙丘、远山、碎石、枯灌木、营帐、旗帜、三架攻城梯、带棚冲车、简化投石车、篝火和火把。

红衣攻城方与蓝绿守军共 50 人，姿态覆盖挥剑、持盾、持矛、攀梯、射箭与倒地。

## 场景统计

来自 `scene_report.json` 的实测数据：

- 对象总数：8541
- 士兵：攻城方 30 人，守军 20 人
- 姿态分布：sword 14、spear 12、strike 7、archer 7、climb 6、fallen 4
- 渲染：Cycles，GPU，1920 × 1200
- 外部素材：0

## 文件

- `qasr_al_raml.blend`：可编辑的 Blender 工程，包含相机、灯光、分组模型、程序化材质与内嵌生成脚本。
- `build_desert_siege.py`：完整场景生成脚本。
- `finalize_scene.py`：收尾处理。
- `scene_report.json`：实际生成数量和渲染配置。
- `preview_hd.png`：1920 × 1200 最终渲染。

## 使用

用 Blender 5.2 打开 `qasr_al_raml.blend`，小键盘 `0` 切换最终相机，`F12` 重新渲染。模型按地形、城堡、庭院、攻城器械、士兵、营地、气氛、灯光分成八个集合。

在 PowerShell 中重新生成：

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python '.\build_desert_siege.py'
```

加 `-- --preview` 可生成较低分辨率预览。脚本会清空执行时场景中的对象，并将结果保存至脚本所在目录；请在新文件或已有备份的场景中运行。

随机种子固定为 `47`。默认使用 Cycles、AgX 和 OptiX GPU；无可用 OptiX 设备时回退 CPU。

## 模型说明

人物为分部件静态摆姿模型，适合整体战场镜头，未做蒙皮绑定或动作动画。布旗和烟尘采用静帧几何与程序化材质，未进行耗时物理模拟。
