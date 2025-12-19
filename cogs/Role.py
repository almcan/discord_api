import discord
from discord.ext import commands

class Role(commands.Cog, name="Role"):
    # Roleクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        
    # メインとなるroleコマンド
    @commands.hybrid_group(name="role",
                           description="!role add/remove 付与対象名 ロール名",
                           fallback="slasher")
    @commands.has_permissions(administrator=True)
    async def role(self, ctx):
        """
        memberのroleを変更します(管理者のみ変更可)
        """
        # サブコマンドが指定されていない場合、メッセージを送信する。
        if ctx.invoked_subcommand is None:
            await ctx.send('このコマンドにはサブコマンドが必要です。')
    
    # roleコマンドのサブコマンド
    # 指定したユーザーに指定した役職を付与する。
    @role.command(name="add", description="!role add 付与対象名 ロール名")
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        # メンバーがサーバーに存在しない場合のチェック
        if member is None:
            await ctx.send("指定したユーザーはサーバーにいません。")
            return

        # ロール付与処理
        await ctx.send(f"{member}に{role}を付与しました")
        await member.add_roles(role)

    # roleコマンドのサブコマンド
    # 指定したユーザーから指定した役職を剥奪する。
    @role.command(name="remove", description="!role remove 付与対象名 ロール名")
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        # メンバーがサーバーに存在しない場合のチェック
        if member is None:
            await ctx.send("指定したユーザーはサーバーにいません。")
            return

        # ロール剥奪処理
        await ctx.send(f"{member}から{role}を剥奪しました")
        await member.remove_roles(role)
    
    @commands.hybrid_command(name="roletable", description="ロール付与パネルを表示します。")
    async def roletable(self, ctx, *, args: str = "null"):
        """ロール付与パネルを表示します。
        """
        # ロール付与を行うチャンネルのid
        channel_id = ctx.channel.id
        channel = self.bot.get_channel(channel_id)

        embed = discord.Embed(title="役職パネル", description="ボタンを押すとロールが付与されます。ついている場合は削除されます", color=discord.Color.blue())
        view = discord.ui.View(timeout=None)  # Viewインスタンスを作成
        # コマンドを実行したサーバーのGuildオブジェクトを取得
        guild = ctx.guild
        # サーバーのすべてのロールを取得
        roles = guild.roles
        # ロールの情報を出力
        for role in roles:
            if role.name not in ["@everyone", "Bot"] and role.name not in args:
                button = Button(label=f'{role.name}', role_id=role.id)
                view.add_item(button)
        await channel.send(embed=embed, view=view)

class Button(discord.ui.Button):
    """ボタンの継承クラス

    Args:
        label: ロール名
        role_id: そのロールのid
    """
    def __init__(self, *, label='role', role_id, **kwargs):
        super().__init__(label=label, **kwargs)
        self.role_id = role_id
        
    async def callback(self, interaction: discord.Interaction):
        # ボタンを押したユーザーの情報を取得
        member = interaction.user
        # ロールを持っているかチェック
        role = discord.utils.get(member.roles, id=self.role_id)
        if role is None:
            # ユーザーにロールを付与
            role = interaction.guild.get_role(self.role_id)
            await member.add_roles(role)
            await interaction.response.send_message(f"ロール: {role}が付与されました。", ephemeral=True, delete_after=5)
        else:
            await member.remove_roles(role)
            await interaction.response.send_message(f"ロール: {role}が削除されました", ephemeral=True, delete_after=5)


# Bot本体側からコグを読み込む際に呼び出される関数。
async def setup(bot):
    await bot.add_cog(Role(bot))  # RoleにBotを渡してインスタンス化し、Botにコグとして登録する。
