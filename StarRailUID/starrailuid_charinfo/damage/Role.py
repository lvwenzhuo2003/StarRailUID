from typing import Dict

from gsuid_core.logger import logger

from .utils import merge_attribute


async def calculate_damage(
    base_attr: Dict[str, float],
    attribute_bonus: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
    element: str,
    skill_multiplier: float,
    level: int,
):
    logger.info(f'Skill Multiplier: {skill_multiplier}')
    logger.info(f'Skill Type: {skill_type}')
    logger.info(f'Level: {level}')

    attribute_bonus = apply_attribute_bonus(
        attribute_bonus, skill_type, add_skill_type
    )

    merged_attr = await merge_attribute(base_attr, attribute_bonus)

    attack = merged_attr.get('attack', 0)
    logger.info(f'Attack: {attack}')

    damage_reduction = calculate_damage_reduction(level)
    resistance_area = calculate_resistance_area(
        merged_attr, skill_type, add_skill_type, element
    )
    defence_multiplier = calculate_defence_multiplier(level, merged_attr)
    injury_area, element_area = calculate_injury_area(
        merged_attr, skill_type, add_skill_type, element
    )
    damage_ratio = calculate_damage_ratio(
        merged_attr, skill_type, add_skill_type
    )
    critical_damage = calculate_critical_damage(
        merged_attr, skill_type, add_skill_type
    )
    critical_chance = calculate_critical_chance(
        merged_attr, skill_type, add_skill_type
    )

    expected_damage = calculate_expected_damage(
        critical_chance, critical_damage
    )

    damage_cd = calculate_damage_cd(
        attack,
        skill_multiplier,
        damage_ratio,
        injury_area,
        defence_multiplier,
        resistance_area,
        damage_reduction,
    )
    damage_qw = calculate_damage_qw(
        attack,
        skill_multiplier,
        damage_ratio,
        injury_area,
        defence_multiplier,
        resistance_area,
        damage_reduction,
        expected_damage,
    )

    damage_tz = calculate_damage_tz(
        attack,
        skill_multiplier,
        damage_ratio,
        injury_area,
        defence_multiplier,
        resistance_area,
        damage_reduction,
        expected_damage,
        element,
        element_area
    )

    skill_info_list = [damage_cd, damage_qw, damage_tz]

    logger.info(
        f'Critical Damage: {damage_cd} Expected Damage: {damage_qw} Apocalypse Damage: {damage_tz}'
    )

    return skill_info_list


def apply_attribute_bonus(
    attribute_bonus: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
):
    # Apply attribute bonuses to attack and status probability
    for attr in attribute_bonus:
        if 'AttackAddedRatio' in attr and attr.split('AttackAddedRatio')[
            0
        ] in (skill_type, add_skill_type):
            attribute_bonus['AttackAddedRatio'] += attribute_bonus[attr]
        if 'StatusProbabilityBase' in attr and attr.split(
            'StatusProbabilityBase'
        )[0] in (skill_type, add_skill_type):
            attribute_bonus['StatusProbabilityBase'] += attribute_bonus[attr]
    return attribute_bonus


def calculate_damage_reduction(level: int):
    enemy_damage_reduction = 0.1
    return 1 - enemy_damage_reduction


def calculate_resistance_area(
    merged_attr: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
    element: str,
):
    enemy_status_resistance = 0.0
    for attr in merged_attr:
        if 'ResistancePenetration' in attr:
            # 检查是否有某一属性的抗性穿透
            attr_name = attr.split('ResistancePenetration')[0]
            if attr_name in (element, 'AllDamage'):
                logger.info(f'{attr_name}属性有{merged_attr[attr]}穿透加成')
                enemy_status_resistance += merged_attr[attr]
            # 检查是否有某一技能属性的抗性穿透
            skill_name, skillattr_name = (
                attr_name.split('_', 1) if '_' in attr_name else (None, None)
            )
            if skill_name in (
                skill_type,
                add_skill_type,
            ) and skillattr_name in (element, 'AllDamage'):
                enemy_status_resistance += merged_attr[attr]
                logger.info(
                    f'{skill_name}对{skillattr_name}属性有{merged_attr[attr]}穿透加成'
                )
    return 1.0 - (0 - enemy_status_resistance)


def calculate_defence_multiplier(
    level: int,
    merged_attr: Dict[str, float],
):
    ignore_defence = merged_attr.get('ignore_defence', 1.0)
    enemy_defence = (level * 10 + 200) * ignore_defence
    return (level * 10 + 200) / (level * 10 + 200 + enemy_defence)


def calculate_injury_area(
    merged_attr: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
    element: str,
):
    injury_area = 0.0
    element_area = 0.0
    for attr in merged_attr:
        if 'DmgAdd' in attr and attr.split('DmgAdd')[0] in (
            skill_type,
            add_skill_type,
        ):
            injury_area += merged_attr[attr]
    for attr in merged_attr:
        attr_name = attr.split('DmgAdd')[0]
        if 'AddedRatio' in attr and attr_name in (
            element,
            'AllDamage',
        ):
            if attr_name == element:
                element_area += merged_attr[attr]
            injury_area += merged_attr[attr]
    return injury_area + 1, element_area


def calculate_damage_ratio(
    merged_attr: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
):
    damage_ratio = merged_attr.get('DmgRatio', 0)
    for attr in merged_attr:
        if '_DmgRatio' in attr and attr.split('_')[0] in (
            skill_type,
            add_skill_type,
        ):
            damage_ratio += merged_attr[attr]
    return damage_ratio + 1


def calculate_critical_damage(
    merged_attr: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
):
    if skill_type == 'DOT':
        return 0.0
    critical_damage_base = merged_attr.get('CriticalDamageBase', 0)
    for attr in merged_attr:
        if '_CriticalDamageBase' in attr and attr.split('_')[0] in (
            skill_type,
            add_skill_type,
        ):
            critical_damage_base += merged_attr[attr]
    return critical_damage_base + 1


def calculate_critical_chance(
    merged_attr: Dict[str, float],
    skill_type: str,
    add_skill_type: str,
):
    critical_chance_base = merged_attr['CriticalChanceBase']
    for attr in merged_attr:
        if '_CriticalChance' in attr and attr.split('_')[0] in (
            skill_type,
            add_skill_type,
        ):
            critical_chance_base += merged_attr[attr]
    return min(1, critical_chance_base)


def calculate_expected_damage(
    critical_chance_base: float,
    critical_damage_base: float,
):
    return critical_chance_base * critical_damage_base + 1


def calculate_damage_cd(
    attack: float,
    skill_multiplier: float,
    damage_ratio: float,
    injury_area: float,
    defence_multiplier: float,
    resistance_area: float,
    damage_reduction: float,
):
    return (
        attack
        * skill_multiplier
        * damage_ratio
        * injury_area
        * defence_multiplier
        * resistance_area
        * damage_reduction
    )


def calculate_damage_qw(
    attack: float,
    skill_multiplier: float,
    damage_ratio: float,
    injury_area: float,
    defence_multiplier: float,
    resistance_area: float,
    damage_reduction: float,
    expected_damage: float,
):
    return (
        attack
        * skill_multiplier
        * damage_ratio
        * injury_area
        * defence_multiplier
        * resistance_area
        * damage_reduction
        * expected_damage
    )


def calculate_damage_tz(
    attack: float,
    skill_multiplier: float,
    damage_ratio: float,
    injury_area: float,
    defence_multiplier: float,
    resistance_area: float,
    damage_reduction: float,
    expected_damage: float,
    element: str,
    element_area: float
):
    injury_add_tz = 0.0
    attack_tz = attack + attack * (1 + 2.144) + 0
    if element == 'Imaginary':
        injury_add_tz = 0.12
    damage_tz = (
        attack_tz
        * skill_multiplier
        * damage_ratio
        * (injury_area + injury_add_tz + 2.326)
        * defence_multiplier
        * resistance_area
        * damage_reduction
        * (expected_damage + 1.594)
        * 10
    )
    element_area = 0 if element == 'Thunder' else 0
    damage_tz_fj = (
        attack_tz
        * 0.44
        * damage_ratio
        * (injury_area + 2.326 + element_area)
        * defence_multiplier
        * resistance_area
        * damage_reduction
        * (expected_damage + 1.594)
        * 10
    )
    damage_tz += damage_tz_fj
    return damage_tz
