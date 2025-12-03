from pyecs import World, Component, EntityID
from typing import List


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Position(x={self.x}, y={self.y})"


class Velocity(Component):
    def __init__(self, dx: float = 0.0, dy: float = 0.0):
        self.dx = dx
        self.dy = dy

    def __repr__(self):
        return f"Velocity(dx={self.dx}, dy={self.dy})"


class Health(Component):
    def __init__(self, value: int = 100):
        self.value = value

    def __repr__(self):
        return f"Health(value={self.value})"


class Name(Component):
    def __init__(self, name: str = ""):
        self.name = name

    def __repr__(self):
        return f"Name(name={self.name})"


def test_basic_query():
    """测试基本查询功能"""
    print("=== 测试基本查询 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))
    e2 = world.spawn(Position(3, 4), Velocity(1, 1))
    e3 = world.spawn(Position(5, 6), Health(50), Name("Player"))
    e4 = world.spawn(Velocity(2, 2), Health(75))

    # 查询所有带有Position组件的实体
    pos_entities = world.query(Position)
    print(f"带有Position的实体: {pos_entities}")
    assert e1 in pos_entities and e2 in pos_entities and e3 in pos_entities
    assert e4 not in pos_entities
    print("✓ 基本查询测试通过")

    # 查询同时带有Position和Health的实体
    pos_health_entities = world.query(Position, Health)
    print(f"带有Position和Health的实体: {pos_health_entities}")
    assert e1 in pos_health_entities and e3 in pos_health_entities
    assert e2 not in pos_health_entities and e4 not in pos_health_entities
    print("✓ 多组件查询测试通过")


def test_without_query():
    """测试排除查询功能"""
    print("\n=== 测试排除查询 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))
    e2 = world.spawn(Position(3, 4), Velocity(1, 1))  # 没有Health
    e3 = world.spawn(Position(5, 6), Health(50), Name("Player"))
    e4 = world.spawn(Velocity(2, 2), Health(75))  # 没有Position

    # 查询带有Position但没有Health的实体
    pos_no_health = world.query(Position, without=[Health])
    print(f"带有Position但没有Health的实体: {pos_no_health}")
    assert e2 in pos_no_health
    assert e1 not in pos_no_health and e3 not in pos_no_health
    print("✓ 排除查询测试通过")


def test_changed_query():
    """测试变化查询功能"""
    print("\n=== 测试变化查询 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))
    e2 = world.spawn(Position(3, 4), Velocity(1, 1))

    # 初始tick是0
    print(f"初始tick: {world.tick}")

    # 查询所有带Position的实体
    initial_pos = world.query(Position)
    print(f"初始带Position的实体: {initial_pos}")

    # 修改实体组件，增加tick
    world.tick += 1
    world.add_component(e1, Velocity(0.5, 0.5))  # e1添加Velocity组件

    # 查询在上一个tick后变化的带Position的实体
    changed_pos = world.query(Position, changed={Velocity})
    print(f"变化了Velocity的带Position实体: {changed_pos}")
    # e1应该在结果中，因为它添加了Velocity组件
    assert e1 in changed_pos
    print("✓ 变化查询测试通过")


def test_empty_query():
    """测试空查询"""
    print("\n=== 测试空查询 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))
    e2 = world.spawn(Velocity(1, 1))

    # 空查询应返回所有实体
    all_entities = world.query()
    print(f"所有实体: {all_entities}")
    assert len(all_entities) == 2
    print("✓ 空查询测试通过")


def test_no_match_query():
    """测试无匹配查询"""
    print("\n=== 测试无匹配查询 ===")
    world = World()

    # 创建只有Position的实体
    e1 = world.spawn(Position(1, 2))

    # 查询带有Health的实体（应该没有）
    health_entities = world.query(Health)
    print(f"带Health的实体: {health_entities}")
    assert len(health_entities) == 0
    print("✓ 无匹配查询测试通过")


def test_complex_query():
    """测试复杂查询"""
    print("\n=== 测试复杂查询 ===")
    world = World()

    # 创建各种实体
    e1 = world.spawn(Position(1, 2), Health(100), Name("Player1"))  # 有所有组件
    e2 = world.spawn(Position(3, 4), Velocity(1, 1))  # 有Position但没有Health
    e3 = world.spawn(Position(5, 6), Health(50), Name("Player2"))  # 有Position和Health，没有Velocity
    e4 = world.spawn(Velocity(2, 2), Health(75))  # 没有Position
    e5 = world.spawn(Position(7, 8), Health(25), Velocity(0.5, 0.5))  # 有Position, Health, Velocity

    # 查询带有Position和Health但没有Velocity的实体
    complex_query = world.query(Position, Health, without=[Velocity])
    print(f"带Position和Health但没有Velocity的实体: {complex_query}")
    assert e1 in complex_query and e3 in complex_query
    assert e2 not in complex_query and e4 not in complex_query and e5 not in complex_query
    print("✓ 复杂查询测试通过")


def test_archetype_management():
    """测试原型管理 - 修正理解"""
    print("\n=== 测试原型管理 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))
    e2 = world.spawn(Position(3, 4), Health(50))

    # 初始查询
    pos_health_entities = world.query(Position, Health)
    print(f"初始带Position和Health的实体: {pos_health_entities}")
    assert len(pos_health_entities) == 2

    # 给e1添加Velocity组件，使其移动到新原型
    world.add_component(e1, Velocity(1, 1))
    print(f"给e1添加Velocity后，e1的组件: {list(world.entity_components[e1].keys())}")

    # 再次查询带Position和Health的实体
    # 注意：e1仍然具有Position和Health组件，所以它应该仍在结果中
    pos_health_entities_after = world.query(Position, Health)
    print(f"添加Velocity后带Position和Health的实体: {pos_health_entities_after}")

    # 修正理解：e1仍然应该在结果中，因为它仍然具有Position和Health
    # 我们可以进一步验证e1现在属于不同的原型
    e1_archetype = world.entity_archetype[e1]
    e2_archetype = world.entity_archetype[e2]

    print(f"e1的原型组件: {e1_archetype.components}")
    print(f"e2的原型组件: {e2_archetype.components}")

    # e1现在应该有Position, Health, Velocity三个组件的原型
    # e2仍然只有Position, Health的原型
    assert len(e1_archetype.components) == 3  # Position, Health, Velocity
    assert len(e2_archetype.components) == 2  # Position, Health
    assert e1 in pos_health_entities_after  # e1仍然有Position和Health
    assert e2 in pos_health_entities_after  # e2仍然有Position和Health

    print("✓ 原型管理测试通过（e1和e2在不同原型中，但都满足查询条件）")


def test_archetype_exclusive_query():
    """测试原型独占查询 - 只有特定组件的实体"""
    print("\n=== 测试原型独占查询 ===")
    world = World()

    # 创建实体
    e1 = world.spawn(Position(1, 2), Health(100))  # 只有Position和Health
    e2 = world.spawn(Position(3, 4), Health(50), Velocity(1, 1))  # 有Position, Health, Velocity

    # 查询只有Position和Health的实体（不包含Velocity）
    pos_health_only = world.query(Position, Health, without=[Velocity])
    print(f"只有Position和Health的实体: {pos_health_only}")
    assert e1 in pos_health_only
    assert e2 not in pos_health_only
    print("✓ 原型独占查询测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始测试ECS Query功能...")

    try:
        test_basic_query()
        test_without_query()
        test_changed_query()
        test_empty_query()
        test_no_match_query()
        test_complex_query()
        test_archetype_management()
        test_archetype_exclusive_query()

        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
