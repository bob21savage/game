        import random
        from dataclasses import dataclass
        from typing import List, Dict
        import json
        import os

        @dataclass
        class Character:
            name: str
            char_class: str
            level: int = 1
            hp: int = 10
            max_hp: int = 10
            strength: int = 10
            dexterity: int = 10
            constitution: int = 10
            intelligence: int = 10
            wisdom: int = 10
            charisma: int = 10
            inventory: List[str] = None

            def __post_init__(self):
                if self.inventory is None:
                    self.inventory = []

            def roll_attribute(self):
                """Roll 4d6, drop lowest, sum the rest"""
                rolls = sorted([random.randint(1, 6) for _ in range(4)])
                return sum(rolls[1:])  # Drop lowest roll

            def generate_stats(self):
                """Generate random stats for character"""
                self.strength = self.roll_attribute()
                self.dexterity = self.roll_attribute()
                self.constitution = self.roll_attribute()
                self.intelligence = self.roll_attribute()
                self.wisdom = self.roll_attribute()
                self.charisma = self.roll_attribute()
                self.max_hp = 10 + (self.constitution - 10) // 2
                self.hp = self.max_hp

        class Game:
            def __init__(self):
                self.character = None
                self.monsters = {
                    'Goblin': {'hp': 7, 'damage': '1d6', 'xp': 50},
                    'Skeleton': {'hp': 13, 'damage': '1d6', 'xp': 100},
                    'Orc': {'hp': 15, 'damage': '1d8', 'xp': 150}
                }
                self.locations = {
                    'town': ['shop', 'inn', 'temple'],
                    'dungeon': ['entrance', 'dark corridor', 'treasure room']
                }
                self.current_location = 'town'

            def create_character(self):
                """Create a new character"""
                print("\nWelcome to Character Creation!")
                name = input("Enter your character's name: ")

                print("\nAvailable Classes:")
                classes = ['Fighter', 'Wizard', 'Rogue']
                for i, c in enumerate(classes, 1):
                    print(f"{i}. {c}")

                while True:
                    choice = input("\nChoose your class (1-3): ")
                    if choice.isdigit() and 1 <= int(choice) <= 3:
                        char_class = classes[int(choice) - 1]
                        break
                    print("Invalid choice. Please choose 1-3.")

                self.character = Character(name=name, char_class=char_class)
                self.character.generate_stats()

                if char_class == 'Fighter':
                    self.character.inventory.extend(['Longsword', 'Shield', 'Chain Mail'])
                elif char_class == 'Wizard':
                    self.character.inventory.extend(['Staff', 'Spellbook', 'Robes'])
                else:  # Rogue
                    self.character.inventory.extend(['Dagger', 'Leather Armor', 'Thieves Tools'])

                print("\nCharacter created successfully!")
                self.show_character_stats()

            def show_character_stats(self):
                """Display character stats"""
                if not self.character:
                    print("No character exists yet!")
                    return

                print(f"\n=== {self.character.name} the {self.character.char_class} ===")
                print(f"Level: {self.character.level}")
                print(f"HP: {self.character.hp}/{self.character.max_hp}")
                print("\nAttributes:")
                print(f"Strength: {self.character.strength}")
                print(f"Dexterity: {self.character.dexterity}")
                print(f"Constitution: {self.character.constitution}")
                print(f"Intelligence: {self.character.intelligence}")
                print(f"Wisdom: {self.character.wisdom}")
                print(f"Charisma: {self.character.charisma}")
                print("\nInventory:")
                for item in self.character.inventory:
                    print(f"- {item}")

            def roll_dice(self, dice_str):
                """Roll dice in format 'XdY' (e.g., '2d6')"""
                num, sides = map(int, dice_str.split('d'))
                return sum(random.randint(1, sides) for _ in range(num))

            def combat(self, monster_name):
                """Handle combat with a monster"""
                if not self.character:
                    print("Create a character first!")
                    return

                monster = self.monsters[monster_name]
                monster_hp = monster['hp']

                print(f"\nCombat started with {monster_name}!")
                print(f"{monster_name} HP: {monster_hp}")

                while monster_hp > 0 and self.character.hp > 0:
                    # Player turn
                    input("\nPress Enter to attack...")
                    if 'Weapon' in self.character.inventory:
                        # Assuming you have a way to identify the weapon in inventory
                        weapon_damage = self.roll_dice('1d10')  # Example weapon damage
                        damage = weapon_damage
                        print(f"You hit the {monster_name} for {damage} damage!")
                    else:
                        damage = self.roll_dice('1d8')  # Basic attack
                        print(f"You hit the {monster_name} for {damage} damage!")
                    monster_hp -= damage

                    if monster_hp <= 0:
                        print(f"\nYou defeated the {monster_name}!")
                        self.character.level += 1
                        print(f"Level up! You are now level {self.character.level}")
                        return True

                    # Monster turn
                    # Calculate monster damage based on player's strength
                    strength_bonus = max(0, (self.character.strength - 10) // 2)
                    monster_damage_base = self.roll_dice(monster['damage'])
                    monster_damage = monster_damage_base + strength_bonus

                    self.character.hp -= monster_damage
                    print(f"{monster_name} hits you for {monster_damage} damage!")
                    print(f"Your HP: {self.character.hp}/{self.character.max_hp}")

                    if self.character.hp <= 0:
                        print("\nYou have been defeated!")
                        return False

            def rest(self):
                """Rest to recover HP"""
                if not self.character:
                    print("Create a character first!")
                    return

                self.character.hp = self.character.max_hp
                print("You take a long rest and recover all your HP.")
                print(f"HP restored to {self.character.hp}")

            def save_game(self):
                """Save the game state"""
                if not self.character:
                    print("No character to save!")
                    return

                save_data = {
                    'character': {
                        'name': self.character.name,
                        'char_class': self.character.char_class,
                        'level': self.character.level,
                        'hp': self.character.hp,
                        'max_hp': self.character.max_hp,
                        'strength': self.character.strength,
                        'dexterity': self.character.dexterity,
                        'constitution': self.character.constitution,
                        'intelligence': self.character.intelligence,
                        'wisdom': self.character.wisdom,
                        'charisma': self.character.charisma,
                        'inventory': self.character.inventory
                    },
                    'location': self.current_location
                }

                with open('save_game.json', 'w') as f:
                    json.dump(save_data, f)
                print("Game saved successfully!")

            def load_game(self):
                """Load the game state"""
                if not os.path.exists('save_game.json'):
                    print("No saved game found!")
                    return

                with open('save_game.json', 'r') as f:
                    save_data = json.load(f)

                char_data = save_data['character']
                self.character = Character(
                    name=char_data['name'],
                    char_class=char_data['char_class'],
                    level=char_data['level'],
                    hp=char_data['hp'],
                    max_hp=char_data['max_hp'],
                    strength=char_data['strength'],
                    dexterity=char_data['dexterity'],
                    constitution=char_data['constitution'],
                    intelligence=char_data['intelligence'],
                    wisdom=char_data['wisdom'],
                    charisma=char_data['charisma'],
                    inventory=char_data['inventory']
                )
                self.current_location = save_data['location']
                print("Game loaded successfully!")
                self.show_character_stats()

        def main():
            game = Game()

            while True:
                print("\n=== D&D Game Menu ===")
                print("1. Create New Character")
                print("2. Show Character Stats")
                print("3. Fight Monster")
                print("4. Rest")
                print("5. Save Game")
                print("6. Load Game")
                print("7. Quit")

                choice = input("\nEnter your choice (1-7): ")

                if choice == '1':
                    game.create_character()
                elif choice == '2':
                    game.show_character_stats()
                elif choice == '3':
                    if not game.character:
                        print("Create a character first!")
                        continue

                    print("\nAvailable Monsters:")
                    monsters = list(game.monsters.keys())
                    for i, monster in enumerate(monsters, 1):
                        print(f"{i}. {monster}")

                    monster_choice = input("\nChoose a monster to fight (1-3): ")
                    if monster_choice.isdigit() and 1 <= int(monster_choice) <= 3:
                        monster = monsters[int(monster_choice) - 1]
                        game.combat(monster)
                    else:
                        print("Invalid choice!")
                elif choice == '4':
                    game.rest()
                elif choice == '5':
                    game.save_game()
                elif choice == '6':
                    game.load_game()
                elif choice == '7':
                    print("Thanks for playing!")
                    break
                else:
                    print("Invalid choice! Please choose 1-7.")

        if __name__ == "__main__":
            main()