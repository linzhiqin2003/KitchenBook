# 第 20 章 — 软件测试

## 章节概览

这是整门课的最后一讲，由 Jo Hallett 主讲。它正面回答一个学生憋了一整年的问题：*"我怎么知道我写对了？"* 老实说，证明代码"正确"是非常困难的——哪怕一个看起来平平无奇的、对 `int` 数组求 `mean()` 的函数，都会在三个地方悄悄翻车：取整问题（`int` 整除）、浮点精度问题（`IEEE 754`）、溢出问题（`INT_MAX`）。等你把这些都修好，还得在"先求和再除"和"边走边除"之间做选择，前者快、后者数值稳定——又是一个 trade-off。

这一讲的立场很清楚：*我们没办法保证绝对真理，所以应该针对已知的局限去做工程。* 整章基本上是一次按"严谨度和成本"递增顺序的技术巡礼：

1. `assert`（最便宜，仅用于 debug 阶段的 sanity check）
2. **Unit testing**（单元测试）—— Python 用 `pytest`
3. **Behavioural / Acceptance testing**（行为测试 / 验收测试）—— Cucumber，配合用自然英语写的 `.feature` 文件
4. **Property testing**（属性测试）—— QuickCheck（Haskell）/ `pytest-quickcheck`
5. **Fuzz testing**（模糊测试）—— AFL++
6. **Formal methods**（形式化方法）—— Lean 4、seL4（"核选项"）

幻灯片传递的关键信息是：大多数工程师做到 unit + behavioural + property 这三层就停了。形式化证明是"中等难度问题就要花一个 PhD 那么多力气"，只用在飞机、AWS 网络、内核（seL4）、密码学这种地方。课程实际动手教的框架是 **`pytest`**。

## 核心知识

### 为什么要测试，bug 的代价

哪怕"看起来对"的代码，根据语言、类型系统、硬件、输入的不同，会以各种方式出错。幻灯片给了 `mean()` 的五次迭代版本，每一版都能编译能跑，但每一版都隐藏着某种细节缺陷（整数除法、format specifier 错配、浮点四舍五入、整数溢出）。没有测试你根本意识不到。

Quality Assurance（质量保证）是软件工程的一整个分支。它存在的理由是：你的代码*现在*能通过测试、并且*以后*不会回退（regression），这才是生产级代码的最低门槛。

### 测试金字塔（行业背景，幻灯片没画）

幻灯片没有画经典的测试金字塔（底层是大量 unit test，顶层是少量 end-to-end test），但它的论述顺序其实就是按金字塔来的：unit test 是主力军，行为测试 / 验收测试在它上面，fuzz 和形式化方法稀少而昂贵。

### 测试分类

| 类别 | 检查的是什么 | 幻灯片是否覆盖 |
|---|---|---|
| **Unit** | 单个函数 / 类对一组已知输入的行为 | 是 —— pytest 那一节 |
| **Integration** | 多个 unit 联调 | 隐式覆盖（cribbage lab 把模块串起来测） |
| **System / End-to-end** | 把整个程序当黑盒来测 | 没有显式覆盖 |
| **Regression** | 老 bug 不要再回来（"以前能过的测试现在挂了"） | 是 —— 列为生产最低标准 |
| **Acceptance / Behavioural (BDD)** | 由客户写 spec、由代码验证 | 是 —— Cucumber 那一节 |
| **Property** | 普世声明对*任意*输入都成立 | 是 —— QuickCheck 那一节 |
| **Fuzz** | 随机 / 损坏的输入不会让程序崩 | 是 —— AFL++ |
| **Performance** | 速度 / 内存的上下界 | 只在"形式化证明 bound"那里顺带提到 |

### black-box vs white-box

幻灯片没把这两个词单独拎成标题，但两种风格都出现了：
- *black-box*：feature 文件里的场景描述（"base = 4，power = 7，answer = 16384"）—— 只关心输入输出。
- *white-box*：fuzzer "对代码做插桩…试图找出能触发每一条 conditional 分支的输入"。属性测试介于两者之间。

### TDD 的 red-green-refactor

幻灯片没明说这个词。但隐含的循环就是"写测试 → 跑 → 修代码 → 再跑"—— `power2.py` 的失败正是触发了这样一次调查。

### 课程里实际教的 Python 框架

**`pytest`**，运行命令是 `python -m pytest`。幻灯片明确把它跟"自己用 `if` 语句拼出一个 ad-hoc 测试模式"的做法做了对比。截图里看到的 plugin 有 `pytest-asyncio` 和 `pytest-mock`。Lab 还额外推荐了 `pytest-quickcheck`（属性测试）和 `behave`（BDD）。

`unittest` *不在*课程教学范围内。

### assertion 风格

直接用 Python 内置的 `assert` 写在测试方法里。pytest 会把 assertion 重写，所以失败时两边的值都打印出来：

```
>       assert power(1,100) == 5
E       assert None == 5
E        +  where None = power(1, 100)
```

如果要断言抛出某种异常，用 context manager `pytest.raises`：

```python
def test_knownerror(self):
    with pytest.raises(AssertionError):
        power(2, -3)
```

测试可以放在 `class TestPower` 里，也可以写成裸的 `def test_*` 函数；pytest 两种都能发现。例子里把测试和被测代码放在了同一个文件里——上课讲解可以这么搞，正经项目里不要。

### fixture

幻灯片没讲。属于 pytest 的标准知识：fixture 就是一个用 `@pytest.fixture` 装饰的函数，它的返回值会被注入到任何把它名字写成参数的测试里。常见用途比如，给每个 cribbage 测试准备一份新鲜的 `Deck()` 或 `Game([Martin(), Martin()])`。

### parametrize

幻灯片也没讲。属于 pytest 的标准知识：`@pytest.mark.parametrize("base,exp,expected", [(4,7,16384), (2,10,1024), (3,0,1)])` 会让同一段测试体每个 tuple 跑一次。

### Mock 与依赖注入

幻灯片没覆盖。`pytest-mock` 这个 plugin 在截图里出现过，但没演示。cribbage lab 反而硬逼你面对这个问题：`agents.Martin.choose_play` 调用了 `random.shuffle`，所以你想测一个确定性结果，要么得 seed `random`，要么得 monkey-patch `random.shuffle`，要么得注入一个假 agent —— 这正是 lab 那句提示*"有时候你需要修改代码本身才能让它好测"*的意思。

### coverage

`coverage.py` 这个名字在幻灯片里*没*出现。最接近的描述是 AFL++ 那段："对代码做插桩…找出能触发每一条 conditional 分支的输入"。从精神上讲那就是 branch coverage，但驱动方式是 fuzzer 而不是 coverage 工具。

### 测试设计技巧

幻灯片没点名 **equivalence partitioning**（等价类划分）、**boundary value analysis**（边界值分析）或 decision table。但它展示了底层直觉：QuickCheck 的例子刻意去探边界 —— 用 `0` 当 base、用 `1` 当 exponent、负 base 配奇数 exponent、`INT_MAX` overflow。`power(2,-3)` 这个测试就是"负 exponent 必须报错"这一等价类的单元素代表。

### Property-based testing（hypothesis）

属性测试是大段的内容，但幻灯片演示用的是 **QuickCheck**（Haskell），不是 Python 的 `hypothesis`。Lab 指向 **`pytest-quickcheck`**。概念动作是一样的：

1. 提出一个普世性质：*"对任意 base 和 exponent > 0，`b ** e >= b`"*。
2. 让框架自己生成随机输入。
3. 失败时，框架会**收缩（shrink）**到一个最小反例（`*** Failed! Falsified (after 18 tests and 5 shrinks): 0 1`）。

幻灯片借此暴露出来的边界场景：`base = 0`、负 base + 奇 exponent、定宽整数 overflow（`8^21 = -9223372036854775808`）。

### CI 中的测试

CI 没有正面覆盖。Lab 的"Bonus stuff"里推了个邻近实践：装一个 Git pre-commit hook，commit 前跑一遍测试套件，挂了就拒绝 commit。本质上就是把 CI 装到了开发者自己的机器上。

### Fuzz testing

往程序里塞随机 / 损坏的输入找崩溃；带插桩的 fuzzer 还会追求覆盖每一条路径。点名工具：**AFL++**（`apfplus.plus`）。

### 形式化方法

`Lean 4` 证明助手；`seL4` "你怎么都黑不进去的 OS"是头条成功案例。Bath 的本地联系：Rod Chapman 在 AWS 用形式化方法证明网络属性。幻灯片话也说得直白：成本是天文数字，只有在"出问题等于灾难"的场景下才值得（航空、超大规模基础设施、root of trust、密码学）。

## pytest 速查

```bash
# 跑当前目录下所有测试
python -m pytest

# 跑特定文件 / 特定 test
python -m pytest path/to/file.py
python -m pytest path/to/file.py::TestPower::test_knowngood

# 更详细的输出，遇到第一个失败就停
python -m pytest -v -x
```

```python
# 1. 裸函数风格的测试（pytest 推荐）
def test_knowngood():
    assert power(4, 7) == 16384

# 2. 用 class 分组（幻灯片里用的就是这种）
class TestPower:
    def test_knowngood(self):
        assert power(4, 7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2, -3)

# 3. 断言抛出异常
with pytest.raises(ValueError, match="negative"):
    power(2, -3)

# 4. fixture（幻灯片没讲，属常规实践）
import pytest

@pytest.fixture
def fresh_deck():
    from cribbage.deck import Deck
    return Deck()

def test_deck_has_52(fresh_deck):
    assert len(fresh_deck._cards) == 52

# 5. parametrize（幻灯片没讲，属常规实践）
@pytest.mark.parametrize("b,e,expected", [
    (4, 7, 16384),
    (2, 10, 1024),
    (3, 0, 1),
])
def test_power_table(b, e, expected):
    assert power(b, e) == expected

# 6. 用 pytest-quickcheck 写属性测试（lab 推荐）
import pytest_quickcheck   # 注册 marker

@pytest.mark.randomize(b=int, e=int, min_num=1, max_num=20)
def test_power_grows(b, e):
    assert power(b, e) >= b
```

幻灯片里 pytest 的输出格式：

```
============================= test session starts ==============================
platform linux -- Python 3.13.2, pytest-8.3.4, pluggy-1.5.0
plugins: asyncio-0.24.0, mock-3.14.0
collected 3 items
power2.py ..F                                                           [100%]

=================================== FAILURES ===================================
____________________________ TestPower.test_failing ____________________________
>       assert power(1,100) == 5
E       assert None == 5
E        +  where None = power(1, 100)
========================= 1 failed, 2 passed in 0.01s ==========================
```

一个点 `.` 是 passing，`F` 是 failing，`E` 是 errored，`s` 是 skipped。

## power.py vs power2.py

这两个文件 99% 一模一样：

```python
# power.py
class TestPower:
    def test_knowngood(self):
        assert power(4,7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2,-3)
```

```python
# power2.py —— 末尾多加了一个方法
class TestPower:
    def test_knowngood(self):
        assert power(4,7) == 16384

    def test_knownerror(self):
        with pytest.raises(AssertionError):
            power(2,-3)

    def test_failing(self):           # <-- 新加的
        assert power(1,100) == 5
```

所以 `power2.py` **不是** `power.py` "为了好测而重新设计"的版本。它就是同一份代码，故意多加了一个*新*测试，专门用来暴露一个真实存在的 bug。这是个教学小把戏，不是 refactor。

新测试揭示的东西比测试本身还有意思。回头看实现：

```python
def power(base, exponent):
    assert(exponent >= 0)
    if exponent == 0:
        return 1
    if exponent == 1:
        return base
    if exponent & 1 == 1:
        return base * power(base*base, (exponent-1)//2)
    # 注意：偶数 exponent 那一支根本没有 return 语句！
```

本应处理偶数 exponent 那一支的递归 `power(base*base, exponent//2)` **被漏掉了**。所以只要拿一个 ≥ 2 的偶数 exponent 调 `power`，Python 就会从函数末尾掉出来，隐式返回 `None`。`power(1, 100)` 走的就是这条路 —— `100` 是偶数 —— 函数返回 `None`，新加的测试用 `assert None == 5` 失败，这个失败直接把开发者指向了那个被漏掉的分支。前一张幻灯片上的 C 版本*是有*那个对应的第四分支的，所以这是从 C 移植到 Python 时引入的、Python 独有的 bug。

教学要点是：`power.py` 的测试套件（`test_knowngood` 只检查了 `power(4,7)`，那是个*奇数* exponent 路径）给了一种虚假的安全感。多加*一个* case 就触到了一条之前没被覆盖的分支，bug 立刻就掉出来了。这就是 regression test 和 branch coverage 的微缩演示。

## Lab 实操

来源：`lab/README.org`、`lab/cribbage/` 这个 package、`lab/cribbage.py` 入口。

**目标：** 在一份真实的、故意写得有 bug 的代码里练习写测试。讲师在意的（也是会考的）learning outcome 是"你尝试写过测试"——而不是要你精通某个具体框架。

### 模拟器

`cribbage.py` 是一个五行的入口：

```python
ai = Martin()
human = Martin()
game = Game([human, ai])
game.play()
```

跑 `python3 cribbage.py` 就模拟一局两个 `Martin` agent 之间的对战（`agents.py`），其中 `Martin.choose_play` 是用 `random.shuffle` 随便选一张牌，`choose_discards` 也是随机弃两张。包结构：

```
lab/cribbage/
  __init__.py
  card.py        # Card 类：rank、suit、value、is_black_jack、str/repr
  deck.py        # Deck：构造并发出 52 张牌
  round.py       # Round：手牌、出牌轮、box、弃牌
  game.py        # Game：顶层循环、计分、the play、the hand
  agents.py      # Agent / Martin（随机 AI）/ Human（stdin）
  util.py        # all_equal、subset、str_cards
  scoring/
    __init__.py
    hand.py      # fifteens、pairs、runs、flushes
    play.py      # Play、check_*；Trick/Nob/Fifteen/Pair/Run 各类
```

### 推荐工具链

- `pytest` 写 unit test。
- `pytest-quickcheck` 写 property test。
- 可选 `behave`（Cucumber 的 Python 移植）写 behavioural test —— 不强制。

README 写得很明确：*"我们想要的 learning outcome 是你尝试过写测试，不是要你掌握某个特定框架。"*

### 推荐的 unit / behavioural 测试

来自 `README.org` 的 *Unit or behavioural tests* 一节：

1. 梅花 J 的 `value() == 10`。
2. 红心 J 和黑桃 3 的 `is_black_jack()` 返回 `False`。
3. 一手牌值 4 分时，输出里始终带有 *"and the rest don't score"*。
4. cribbage 最大牌型 —— 四张 5 加一张黑色 J 翻牌 —— 计 27 分。
5. 红心和方块永远以红色打印。
6. 沿 cribbage 棋盘走一圈：外圈走上去，内圈走回来。

对应到代码：

```python
# 1
def test_jack_of_clubs_value_is_10():
    assert Card("JC").value() == 10

# 2
def test_jack_of_hearts_is_not_black_jack():
    assert Card("JH").is_black_jack() is False

def test_three_of_spades_is_not_black_jack():
    assert Card("3S").is_black_jack() is False

# 3 —— 需要 capsys 捕获 print 输出
def test_score_4_says_rest_dont_score(capsys):
    ...
    out = capsys.readouterr().out
    assert "and the rest don't score" in out

# 4 —— 真实 cribbage 里的著名 "29 hand" 是 JH 5S 5C 5D + 5H turn 计 29 分，
#      但 README 明确写的是"四张 5 + 黑 J 翻牌"计 27 分。
#      不管哪种数字：构造这手牌、断言分数。
```

### 推荐的 property 测试

来自 `README.org` 的 *Property tests* 一节：

1. 在 the play 阶段不可能恰好得到 19 分（`game.py: _play_hand`）。
2. 一局结束时，**恰好**有一个玩家分数 > 120。
3. the play 中的 run 长度永远不超过 7 张牌（`scoring/play.py`）。
4. 不可能从 5 张同点数的牌里凑出一对（不可能 —— 每个 rank 只有 4 张）。

这些刚好契合 QuickCheck 的思路：*"对任意随机生成的对局状态，这条不变式必须成立。"*

### 这套练习会暴露出来的 bug

用测试者的眼光读供给的代码，会发现真实存在的缺陷：

- `cribbage/scoring/play.py` 第 39 行：`[PairRoyale(played[-3:])]` 引用了一个未定义的名字 `played`（应当是 `self._played`）。pair-royale 这条路径运行时直接崩。
- `cribbage/scoring/play.py` 第 91 行：`class PairImperiale` 把名字 `"Pair Royale"` 传进了 `super().__init__`，把本来 12 分的 pair imperiale 误标成了 pair royale。
- `cribbage/game.py` 第 168 行：`printf(f"--- Pair imperiale!...")` —— Python 里压根没有 `printf`，应当是 `print`。一旦出现 quad 就崩。
- `cribbage/game.py` 第 119 行：`if play == 31` 拿一个 `Play` 对象去跟 int 比；应当是 `play.count == 31`。
- `cribbage/scoring/hand.py` 第 52 行：拿来比较的是 `card.suit`（method 对象本身）而不是 `card.suit()` —— flush 检测因此整个失效。
- `cribbage/scoring/hand.py`：`flushes()` 返回的是个 `int`（4、5 或 0），但 `game._play_hand` 接着拿它去 `str_cards(flushes)` 迭代 —— 会崩。
- `cribbage/round.py`：`get_box` 被定义了两次（无害，第二个覆盖第一个）。
- `cribbage/card.py`：传进一个 3 字符的 `value`（比如 `"10H"`）时，`self._rank = 10`（变成 int），且 `self._suit` 根本没被设。`Card("10H")` 是坏的。

这正是 README 提醒过的：*"如果你写出了一个怎么都过不了的测试…可能要去改的是代码。"*

### 期望的 coverage

没给具体数字目标。可达成的目标是：把 `card.py`、`scoring/hand.py`、`scoring/play.py` 测充分（这几个文件纯函数、确定性、好测），而 `game.py` 只有在你注入了一个确定性的 agent、让 `random.shuffle` 不再让每一次跑都不一样之后，再去测它。这就是"有时候你需要修改代码本身才能让它好测"那条提示背后的潜台词。

### 加分项

- 把测试套件接进 Git **pre-commit hook**（在 `.git/hooks/pre-commit` 里跑 `python -m pytest`，非 0 退出码就阻止 commit）。README 给了 Git 官方文档关于 hook 的链接。
- 试一下 **Lean Natural Numbers Game**，体验一下形式化证明的感觉：<https://adam.math.hhu.de/#/g/leanprover-community/nng4>

## 易错点与重点

- **看起来"对"的代码也可能是错的。** 那五个 `mean()` 例子是整堂课的脊柱：你必须知道你的代码*是怎么*错的，而不是去问它"对不对"。
- **`assert` 不算测试。** 它只是 debug 阶段的脚手架。一旦 `-DNDEBUG=1`（C）或者 `python -O`，它就消失了，你以为的"检查"就没有了。生产里必须成立的事情，请用真正的测试框架。
- **跑测试用 `python -m pytest`，不是 `pytest`。** 加 `-m` 形式能保证本地 package 在 `sys.path` 上。幻灯片里每一页演示用的都是这个形式。
- **pytest 的输出本身就是文档。** 仔细看那段 failure 块 —— 它把 assertion、两边的值、值是从哪儿来的都打了出来（`+ where None = power(1,100)`）。靠这个不用 debugger 就能定位绝大多数 bug。
- **加*一个*测试就能暴露一整类 bug。** `power2.py` 是这条规律的样板：原本的套件只覆盖了奇数 exponent 路径，整个一支算法分支没人测过。
- **属性测试很强，但前提是你提的那条 property 是对的。** 幻灯片走过这样一个迭代：`b ** e > b` → 在 `0` 上挂 → 限制为正 base → 在定宽整数 overflow 上挂 → 换成 `Integer`。每一次失败要么是在 refine property，要么是在 refine 类型。
- **shrinking 是 property test 最关键的特性。** 一个长度 200 的随机反例没用；一个最小化的反例（`0, 1`）才告诉你该修哪儿。
- **行为测试把 spec 写在客户能懂的语言里。** Cucumber 的 `.feature` 文件是大白话英语，`step_definitions` 把它翻译成代码。好处是 manager 能看懂、（理论上）也能写。
- **fuzzer 和形式化方法是真工具，不是学院摆设** —— 但成本曲线很陡。只在"出一次崩等于几百万美元或几条人命"的时候用。其它情况停在 unit + property 就行。
- **cribbage lab 特别注意：那份代码是故意有 bug 的。** 一个"看起来对"的测试如果挂了，它*多半就是对的*，而你只是发现了一个 defect。开个 issue，或者直接修。
- **有些测试会逼你重新设计代码。** 随机 AI 和绑定 stdin 的人类 agent 没法直接做单元测试。注入一个确定性 agent、seed `random`、或者 monkey-patch —— 这就是 lab 里那条 testability-driven design 的隐藏教学。
- **考试形式提醒**（与测试本身无关，但属于相关上下文）：32 道四选一选择题、open notes、本学期所有 lecture 和 lab 都在考试范围。
