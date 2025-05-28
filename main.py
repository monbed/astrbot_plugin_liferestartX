from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from .core.Life import Life
import random
import os

@register("liferestartX", "monbed", "人生重开模拟器", "1.1.1")
class LifeRestartPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            Life.load(self.data_dir)
        except Exception as e:
            raise

    def genp(self, prop: int) -> dict:
        ps = []
        tmp = prop
        while True:
            for i in range(0, 4):
                if i == 3:
                    ps.append(tmp)
                else:
                    if tmp >= 10:
                        ps.append(random.randint(0, 35))
                    else:
                        ps.append(random.randint(0, tmp))
                tmp -= ps[-1]
            if ps[3] < 10:
                break
            else:
                tmp = prop
                ps.clear()
        return {'CHR': ps[0], 'INT': ps[1], 'STR': ps[2], 'MNY': ps[3]}

    @filter.command("人生重开帮助", alias=['重开帮助'])
    async def help(self, event: AstrMessageEvent):
        help_text = """人生重开模拟器使用帮助
================================

【基础指令】
--------------------------------
• /人生重来：开始新的人生
• /重开：开始新的人生（简写）

【注意事项】
--------------------------------
1. 每次重开都会随机生成不同的天赋和属性
2. 属性包括：颜值、智力、体质、家境
3. 游戏过程会显示人生重要事件
4. 最后会生成人生总结报告

祝你玩得开心！
================================"""
        url = await self.text_to_image(help_text)
        yield event.image_result(url)

    @filter.command("重开", alias=['人生重来'])
    async def remake(self, event: AstrMessageEvent):
        try:
            # 初始化 life
            for attempt in range(3):
                try:
                    life = Life()
                    life.setTalentHandler(lambda ts: random.choice(ts).id)
                    life.setPropertyhandler(self.genp)
                    if life.choose():
                        break
                except Exception:
                    life = None
            if not life:
                yield event.plain_result("初始化人生失败，请稍后再试")
                return

            name = event.get_sender_name()
            # 基本信息头
            header = f"{name}本次重生的基本信息如下：\n\n"
            header += "【你的天赋】\n--------------------------------\n"
            for i, t in enumerate(life.talent.talents, 1):
                header += f"{i}. 天赋：【{t.name}】\n   效果：{t.desc}\n\n"
            header += "【基础属性】\n--------------------------------\n"
            header += f"颜值：{life.property.CHR}\n智力：{life.property.INT}\n体质：{life.property.STR}\n家境：{life.property.MNY}\n\n"
            header += "【人生经历】\n================================\n"

            # 将生成器转换为列表，支持 len()
            events = list(life.run())  # List[List[str]]

            # 按每100年分段发送
            chunk_size = 100
            total = len(events)
            for start in range(0, total, chunk_size):
                segment = events[start:start + chunk_size]
                text = "你的命运正在重启....\n================================\n\n" + header
                # 添加当前段落事件
                for year_events in segment:
                    text += '\n'.join(year_events) + "\n\n"
                # 如果是最后一段，添加总结
                if start + chunk_size >= total:
                    text += "【人生总结】\n================================\n"
                    text += life.property.gensummary() + "\n================================"

                # 生成并发送图片
                url = await self.text_to_image(text)
                yield event.image_result(url)

        except Exception as e:
            yield event.plain_result(f"发生错误：{e}")

    @filter.command(["人生重开开", "人生重开关"])
    async def handle_plugin_switch(self, event: AstrMessageEvent):
        message = event.message_str.strip()
        group_id = str(event.message_obj.group_id)
        enabled = message == "人生重开开"
        await self.set_group_enabled(group_id, enabled)
        yield event.plain_result(f"已{'启用' if enabled else '禁用'}人生重开模拟器")
