#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface graphique moderne pour l'API d'impression thermique
Thème sombre inspiré des interfaces modernes d'applications web
MISE À JOUR: Support ASCII universel pour toutes les imprimantes
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, font, messagebox
import webbrowser
from datetime import datetime
import getpass
import threading
import time

# Ajouter le répertoire parent au path pour les imports entre modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils.config import config, save_config, logger
    from printer.printer_utils import get_printers, print_test
except ImportError:
    print("Erreur: Modules non trouvés. Assurez-vous d'avoir installé le package avec 'pip install -e .'")
    sys.exit(1)

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageGrab
    HAS_PIL = True
except ImportError:
    print("Info: PIL non installé. Certaines fonctionnalités graphiques seront limitées.")
    HAS_PIL = False

# Constantes de couleurs - Thème sombre inspiré de l'image
DARK_BG = "#1a1a2e"  # Fond principal très sombre avec teinte bleue
PRIMARY_COLOR = "#6c5ce7"  # Violet/bleu vif pour les éléments principaux
SECONDARY_COLOR = "#4834d4"  # Violet plus foncé
ACCENT_COLOR = "#a29bfe"  # Violet clair pour les accents
TEXT_COLOR = "#ffffff"  # Texte blanc
SECONDARY_TEXT = "#a0a0a0"  # Texte gris clair
CARD_BG = "#252541"  # Fond des cartes légèrement plus clair que le fond principal
CARD_ACTIVE = "#2f2f50"  # Fond des cartes actives/survolées
SUCCESS_COLOR = "#00b894"  # Vert
WARNING_COLOR = "#fdcb6e"  # Jaune
ERROR_COLOR = "#e17055"  # Rouge-orange

class ModernApp(tk.Tk):
    """Application principale avec thème moderne et interface de style dashboard"""
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre principale
        self.title("Thermal Printer Dashboard - ASCII Universel")
        self.geometry("1000x650")
        self.minsize(900, 600)
        self.configure(bg=DARK_BG)
        
        # Charger les polices
        self.load_fonts()
        
        # Variable pour suivre la page actuelle
        self.current_page = tk.StringVar(value="dashboard")
        
        # Créer la structure principale
        self.setup_layout()
        
        # Définir le style ttk global
        self.setup_styles()
        
        # Liste des imprimantes - DÉPLACÉ AVANT l'affichage du tableau de bord
        self.printers = []
        self.selected_printer_id = None
        self.refresh_printers()
        
        # Afficher la page de tableau de bord - MAINTENANT APRÈS l'initialisation des imprimantes
        self.show_dashboard()
        
        # Configurer les événements de redimensionnement
        self.bind("<Configure>", self.on_resize)
    
    def load_fonts(self):
        """Charger ou définir les polices personnalisées"""
        # Définir les polices personnalisées
        self.font_title = font.Font(family="Segoe UI", size=24, weight="bold")
        self.font_heading = font.Font(family="Segoe UI", size=18, weight="bold")
        self.font_subheading = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_normal = font.Font(family="Segoe UI", size=10)
        self.font_small = font.Font(family="Segoe UI", size=9)
        self.font_button = font.Font(family="Segoe UI", size=10, weight="bold")
    
    def setup_styles(self):
        """Configurer les styles ttk pour une apparence moderne"""
        style = ttk.Style()
        
        # Essayer d'utiliser un thème de base moderne
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # Utiliser le thème par défaut si clam n'est pas disponible
        
        # Fond général
        style.configure(".", 
                       background=DARK_BG, 
                       foreground=TEXT_COLOR, 
                       troughcolor=DARK_BG,
                       selectbackground=PRIMARY_COLOR,
                       selectforeground=TEXT_COLOR,
                       fieldbackground=CARD_BG,
                       borderwidth=0,
                       focuscolor=PRIMARY_COLOR)
        
        # Frame principal
        style.configure("Main.TFrame", background=DARK_BG)
        
        # Frame de carte
        style.configure("Card.TFrame", 
                       background=CARD_BG, 
                       relief="flat",
                       borderwidth=0)
        
        # Menu latéral
        style.configure("Sidebar.TFrame", 
                       background=DARK_BG)
        
        # Boutons
        style.configure("TButton", 
                       background=PRIMARY_COLOR,
                       foreground=TEXT_COLOR,
                       borderwidth=0,
                       focusthickness=0,
                       font=self.font_button,
                       padding=8)
        
        style.map("TButton",
                 background=[("active", SECONDARY_COLOR), 
                            ("pressed", SECONDARY_COLOR)],
                 relief=[("pressed", "flat"), ("!pressed", "flat")])
        
        # Boutons secondaires
        style.configure("Secondary.TButton", 
                       background=CARD_BG,
                       foreground=TEXT_COLOR)
        
        style.map("Secondary.TButton",
                 background=[("active", CARD_ACTIVE), 
                            ("pressed", CARD_ACTIVE)])
        
        # Boutons de menu inactifs
        style.configure("Menu.TButton", 
                       background=DARK_BG,
                       foreground=SECONDARY_TEXT,
                       padding=10,
                       font=self.font_normal)
        
        # Boutons de menu actifs
        style.configure("Menu.Active.TButton", 
                       background=DARK_BG,
                       foreground=TEXT_COLOR,
                       padding=10, 
                       font=self.font_normal)
        
        style.map("Menu.TButton",
                 background=[("active", DARK_BG)],
                 foreground=[("active", TEXT_COLOR)])
        
        style.map("Menu.Active.TButton",
                 background=[("active", DARK_BG)])
        
        # Labels
        style.configure("TLabel", 
                       background=DARK_BG, 
                       foreground=TEXT_COLOR,
                       font=self.font_normal)
        
        # Labels pour les titres
        style.configure("Title.TLabel", 
                       font=self.font_title, 
                       foreground=TEXT_COLOR,
                       background=DARK_BG)
        
        # Labels pour les en-têtes
        style.configure("Heading.TLabel", 
                       font=self.font_heading, 
                       foreground=TEXT_COLOR,
                       background=DARK_BG)
        
        # Labels pour les sous-en-têtes
        style.configure("Subheading.TLabel", 
                       font=self.font_subheading, 
                       foreground=TEXT_COLOR,
                       background=DARK_BG)
        
        # Labels dans les cartes
        style.configure("Card.TLabel", 
                       background=CARD_BG)
        
        # Labels pour les informations secondaires
        style.configure("Secondary.TLabel", 
                       foreground=SECONDARY_TEXT,
                       background=DARK_BG)
        
        # Entrées
        style.configure("TEntry", 
                       foreground=TEXT_COLOR,
                       fieldbackground=CARD_BG,
                       insertcolor=TEXT_COLOR,
                       borderwidth=0,
                       padding=8)
        
        # Barre de séparation
        style.configure("TSeparator", 
                       background=SECONDARY_TEXT)
        
        # Treeview
        style.configure("Treeview", 
                       background=CARD_BG,
                       foreground=TEXT_COLOR,
                       fieldbackground=CARD_BG,
                       borderwidth=0,
                       font=self.font_normal)
        
        style.configure("Treeview.Heading", 
                       background=CARD_ACTIVE,
                       foreground=TEXT_COLOR,
                       relief="flat",
                       borderwidth=0,
                       font=self.font_subheading)
        
        style.map("Treeview",
                 background=[("selected", PRIMARY_COLOR)],
                 foreground=[("selected", TEXT_COLOR)])
        
        # Combobox
        style.configure("TCombobox", 
                      foreground=TEXT_COLOR,
                      background=CARD_BG,
                      fieldbackground=CARD_BG,
                      arrowcolor=TEXT_COLOR)
        
        style.map("TCombobox",
                background=[("readonly", CARD_BG)],
                fieldbackground=[("readonly", CARD_BG)],
                selectbackground=[("readonly", PRIMARY_COLOR)])
    
    def setup_layout(self):
        """Créer la structure de base de l'interface"""
        # Cadre principal
        self.main_frame = ttk.Frame(self, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barre latérale pour la navigation
        self.sidebar = ttk.Frame(self.main_frame, width=200, style="Sidebar.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # Garder la largeur fixe
        
        # Logo et titre
        logo_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        logo_frame.pack(fill=tk.X, padx=10, pady=20)
        
        logo_text = ttk.Label(logo_frame, text="Thermal API", 
                           style="Title.TLabel",
                           font=self.font_heading)
        logo_text.pack(side=tk.LEFT)
        
        # Badge ASCII universel
        ascii_badge = ttk.Label(logo_frame, text="ASCII", 
                             style="Secondary.TLabel",
                             font=self.font_small)
        ascii_badge.pack(side=tk.LEFT, padx=(5, 0))
        
        # Créer les boutons de menu
        self.create_menu()
        
        # Séparateur
        ttk.Separator(self.sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        
        # Informations sur le système
        system_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        system_frame.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)
        
        system_label = ttk.Label(system_frame, text="Version 1.0.0 - ASCII", 
                              style="Secondary.TLabel")
        system_label.pack(anchor=tk.W)
        
        # Conteneur principal pour le contenu
        self.content_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # En-tête avec titre et heure
        self.header_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.header_frame.pack(fill=tk.X, padx=30, pady=(30, 0))
        
        # Salutation
        try:
            username = getpass.getuser().capitalize()
        except:
            username = "utilisateur"
        
        self.greeting_label = ttk.Label(self.header_frame, 
                                     text=f"Hey {username},",
                                     style="Title.TLabel")
        self.greeting_label.pack(anchor=tk.W)
        
        self.subgreeting_label = ttk.Label(self.header_frame, 
                                        text="voici votre tableau de bord d'impression ASCII universel.",
                                        style="Secondary.TLabel",
                                        font=self.font_subheading)
        self.subgreeting_label.pack(anchor=tk.W)
        
        # Cadre pour les différentes pages de contenu
        self.page_container = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.page_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
    
    def create_menu(self):
        """Créer le menu de navigation latéral"""
        menu_items = [
            ("dashboard", "Tableau de bord", self.show_dashboard),
            ("printers", "Imprimantes", self.show_printers),
            ("settings", "Paramètres", self.show_settings),
            ("logs", "Journaux", self.show_logs)
        ]
        
        self.menu_buttons = {}
        
        for item_id, label, command in menu_items:
            button = ttk.Button(self.sidebar, text=label, command=command, style="Menu.TButton")
            button.pack(fill=tk.X, padx=10, pady=5)
            self.menu_buttons[item_id] = button
            
            # Activer le bouton dashboard par défaut
            if item_id == "dashboard":
                button.configure(style="Menu.Active.TButton")
    
    def update_menu_selection(self, selected_id):
        """Mettre à jour la sélection du menu"""
        for item_id, button in self.menu_buttons.items():
            if item_id == selected_id:
                button.configure(style="Menu.Active.TButton")
            else:
                button.configure(style="Menu.TButton")
        
        self.current_page.set(selected_id)
    
    def clear_page_container(self):
        """Effacer le contenu de la page actuelle"""
        for widget in self.page_container.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Afficher la page du tableau de bord - MISE À JOUR ASCII"""
        self.update_menu_selection("dashboard")
        self.clear_page_container()
        
        # Titre de la page
        page_title = ttk.Label(self.page_container, text="Tableau de bord - ASCII Universel", 
                            style="Heading.TLabel")
        page_title.pack(anchor=tk.W, pady=(0, 20))
        
        # Cartes de statistiques
        stats_frame = ttk.Frame(self.page_container, style="Main.TFrame")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Créer des cartes de statistiques
        self.create_stat_card(stats_frame, "Imprimantes", len(self.printers), 0)
        
        default_printer = "Non définie"
        if config.get('default_printer_name'):
            default_printer = config.get('default_printer_name')
        
        # Afficher la largeur de l'imprimante par défaut
        printer_width = config.get('default_printer_width', '58mm')
        self.create_stat_card(stats_frame, "Imprimante par défaut", f"{default_printer}\n({printer_width})", 1)
        
        self.create_stat_card(stats_frame, "Port API", config.get('port', 5789), 2)
        
        # MODIFIÉ: Carte pour l'encodage ASCII universel
        encoding_display = "ASCII (universel)"
        if config.get('force_ascii_for_all', True):
            encoding_display = "ASCII pour toutes"
        else:
            # Fallback au cas où l'ancien système serait encore actif
            current_encoding = config.get('default_encoding', 'ascii')
            if current_encoding == 'ascii':
                encoding_display = "ASCII (universel)"
            else:
                encoding_display = f"{current_encoding} → ASCII"
        
        self.create_stat_card(stats_frame, "Encodage", encoding_display, 3)
        
        # Section des actions rapides
        actions_title = ttk.Label(self.page_container, text="Actions rapides", 
                               style="Subheading.TLabel")
        actions_title.pack(anchor=tk.W, pady=(30, 10))
        
        # Cadre pour les actions
        actions_frame = ttk.Frame(self.page_container, style="Main.TFrame")
        actions_frame.pack(fill=tk.X, pady=10)
        
        # Créer des cartes d'action
        self.create_action_card(actions_frame, "Tester l'impression ASCII", 
                              "Imprimer un ticket de test avec conversion française automatique", 
                              self.test_default_printer, 0)
        
        self.create_action_card(actions_frame, "Ouvrir API dans le navigateur", 
                              "Accéder à l'interface web de l'API", 
                              self.open_browser, 1)
        
        self.create_action_card(actions_frame, "Rafraîchir les imprimantes", 
                              "Rechercher les imprimantes disponibles", 
                              self.refresh_printers, 2)
    
    def show_printers(self):
        """Afficher la page de gestion des imprimantes"""
        self.update_menu_selection("printers")
        self.clear_page_container()
        
        # Titre de la page
        page_title = ttk.Label(self.page_container, text="Gestion des imprimantes - ASCII universel", 
                            style="Heading.TLabel")
        page_title.pack(anchor=tk.W, pady=(0, 20))
        
        # Cadre pour la liste et les actions
        content_frame = ttk.Frame(self.page_container, style="Main.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cadre pour les boutons d'action
        buttons_frame = ttk.Frame(content_frame, style="Main.TFrame")
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        refresh_btn = ttk.Button(buttons_frame, text="Actualiser", 
                              command=self.refresh_printers_view,
                              style="TButton")
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_btn = ttk.Button(buttons_frame, text="Tester ASCII", 
                           command=self.test_selected_printer,
                           style="Secondary.TButton")
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        default_btn = ttk.Button(buttons_frame, text="Définir par défaut", 
                              command=self.set_default_printer,
                              style="Secondary.TButton")
        default_btn.pack(side=tk.LEFT)
        
        # Info ASCII
        ascii_info = ttk.Label(buttons_frame, 
                             text="🎯 Toutes les imprimantes utilisent l'encodage ASCII avec conversion française automatique", 
                             style="Secondary.TLabel", 
                             font=self.font_small)
        ascii_info.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Liste des imprimantes
        tree_frame = ttk.Frame(content_frame, style="Card.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Créer un Treeview
        columns = ("name", "status", "width", "encoding", "port")
        self.printer_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                      selectmode="browse", style="Treeview")
        
        # Définir les en-têtes
        self.printer_tree.heading("name", text="Nom de l'imprimante")
        self.printer_tree.heading("status", text="Statut")
        self.printer_tree.heading("width", text="Largeur")
        self.printer_tree.heading("encoding", text="Encodage")
        self.printer_tree.heading("port", text="Port")
        
        # Définir les largeurs de colonnes
        self.printer_tree.column("name", width=200, anchor=tk.W)
        self.printer_tree.column("status", width=80, anchor=tk.CENTER)
        self.printer_tree.column("width", width=60, anchor=tk.CENTER)
        self.printer_tree.column("encoding", width=70, anchor=tk.CENTER)
        self.printer_tree.column("port", width=120, anchor=tk.W)
        
        # Ajouter un scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.printer_tree.yview)
        self.printer_tree.configure(yscrollcommand=scrollbar.set)
        
        # Placement
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.printer_tree.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Événements
        self.printer_tree.bind("<<TreeviewSelect>>", self.on_printer_select)
        
        # Remplir la liste des imprimantes
        self.update_printer_list()
    
    def update_printer_list(self):
        """Mettre à jour la liste des imprimantes dans la vue - CORRIGÉ ASCII"""
        # Effacer la liste actuelle
        if hasattr(self, 'printer_tree'):
            for item in self.printer_tree.get_children():
                self.printer_tree.delete(item)
            
            # Ajouter les imprimantes
            for printer in self.printers:
                # Déterminer le statut
                status = "Disponible"
                if printer['is_default']:
                    status = "Système"
                if printer['id'] == config.get('default_printer_id'):
                    status = "Par défaut"
                
                # MODIFIÉ: Obtenir la largeur et l'encodage (ASCII par défaut)
                width = printer.get('width', '58mm')
                encoding = printer.get('encoding', 'ascii')  # ASCII par défaut maintenant
                
                # Ajouter à la liste avec l'ID caché à la fin des valeurs
                values = (printer['name'], status, width, encoding, printer['port'], printer['id'])
                
                self.printer_tree.insert("", tk.END, values=values, tags=(status.lower(),))
            
            # Sélectionner l'imprimante par défaut si elle existe
            if config.get('default_printer_id') is not None:
                for item in self.printer_tree.get_children():
                    values = self.printer_tree.item(item, "values")
                    if values and len(values) >= 6 and int(values[5]) == config.get('default_printer_id'):
                        self.printer_tree.selection_set(item)
                        self.printer_tree.see(item)
                        self.selected_printer_id = config.get('default_printer_id')
                        break
    
    def refresh_printers_view(self):
        """Actualiser la vue des imprimantes"""
        self.refresh_printers()
        self.update_printer_list()
    
    def on_printer_select(self, event):
        """Gérer la sélection d'une imprimante"""
        selected_items = self.printer_tree.selection()
        if selected_items:
            item_id = selected_items[0]
            values = self.printer_tree.item(item_id, "values")
            if values and len(values) >= 6:
                self.selected_printer_id = int(values[5])
    
    def show_settings(self):
        """Afficher la page des paramètres - MISE À JOUR ASCII"""
        self.update_menu_selection("settings")
        self.clear_page_container()
        
        # Titre de la page
        page_title = ttk.Label(self.page_container, text="Paramètres - ASCII universel", 
                            style="Heading.TLabel")
        page_title.pack(anchor=tk.W, pady=(0, 20))
        
        # Cadre pour les paramètres
        settings_frame = ttk.Frame(self.page_container, style="Card.TFrame")
        settings_frame.pack(fill=tk.X, pady=10, padx=1, ipady=15)
        
        # Configuration du port
        port_frame = ttk.Frame(settings_frame, style="Card.TFrame")
        port_frame.pack(fill=tk.X, padx=20, pady=10)
        
        port_label = ttk.Label(port_frame, text="Port de l'API:", style="Card.TLabel")
        port_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.port_var = tk.StringVar(value=str(config.get('port', 5789)))
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        port_btn = ttk.Button(port_frame, text="Appliquer", 
                           command=self.apply_port_setting,
                           style="TButton")
        port_btn.pack(side=tk.LEFT)
        
        # Largeur d'imprimante (affichage seulement car détection automatique)
        width_frame = ttk.Frame(settings_frame, style="Card.TFrame")
        width_frame.pack(fill=tk.X, padx=20, pady=10)
        
        width_label = ttk.Label(width_frame, text="Largeur d'imprimante par défaut:", style="Card.TLabel")
        width_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.width_var = tk.StringVar(value=config.get('default_printer_width', '58mm'))
        width_display = ttk.Label(width_frame, textvariable=self.width_var, style="Card.TLabel")
        width_display.pack(side=tk.LEFT)
        
        width_info = ttk.Label(width_frame, 
                             text="(Détecté automatiquement lors de la sélection de l'imprimante)", 
                             style="Card.TLabel", 
                             font=self.font_small)
        width_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # MODIFIÉ: Encodage ASCII universel
        encoding_frame = ttk.Frame(settings_frame, style="Card.TFrame")
        encoding_frame.pack(fill=tk.X, padx=20, pady=10)
        
        encoding_label = ttk.Label(encoding_frame, text="Encodage universel:", style="Card.TLabel")
        encoding_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.encoding_var = tk.StringVar(value=config.get('default_encoding', 'ascii'))
        encoding_combo = ttk.Combobox(encoding_frame, textvariable=self.encoding_var, 
                                    values=["ascii", "cp1252", "cp850", "cp437", "latin1"], 
                                    width=10, state="readonly")
        encoding_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # MODIFIÉ: Info sur l'encodage ASCII universel
        encoding_info = ttk.Label(encoding_frame, 
                                text="(ASCII avec conversion française: café → cafe, €15,50 → EUR15,50)", 
                                style="Card.TLabel", 
                                font=self.font_small)
        encoding_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # ASCII status
        ascii_status_frame = ttk.Frame(settings_frame, style="Card.TFrame")
        ascii_status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ascii_status_label = ttk.Label(ascii_status_frame, text="Mode ASCII universel:", style="Card.TLabel")
        ascii_status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ascii_enabled = config.get('force_ascii_for_all', True)
        ascii_status_text = "✅ Activé (toutes imprimantes)" if ascii_enabled else "❌ Désactivé"
        ascii_status_display = ttk.Label(ascii_status_frame, text=ascii_status_text, style="Card.TLabel")
        ascii_status_display.pack(side=tk.LEFT)
        
        # URL de l'API
        url_frame = ttk.Frame(settings_frame, style="Card.TFrame")
        url_frame.pack(fill=tk.X, padx=20, pady=10)
        
        url_label = ttk.Label(url_frame, text="URL de l'API:", style="Card.TLabel")
        url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        api_url = f"http://localhost:{config.get('port', 5789)}"
        self.url_var = tk.StringVar(value=api_url)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=30, state="readonly")
        url_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        url_btn = ttk.Button(url_frame, text="Ouvrir dans le navigateur", 
                          command=self.open_browser,
                          style="TButton")
        url_btn.pack(side=tk.LEFT)
        
        # Bouton pour enregistrer les paramètres
        save_frame = ttk.Frame(self.page_container, style="Main.TFrame")
        save_frame.pack(fill=tk.X, pady=20)
        
        save_btn = ttk.Button(save_frame, text="Enregistrer tous les paramètres", 
                           command=self.save_all_settings,
                           style="TButton")
        save_btn.pack(side=tk.RIGHT)
    
    def show_logs(self):
        """Afficher la page des journaux"""
        self.update_menu_selection("logs")
        self.clear_page_container()
        
        # Titre de la page
        page_title = ttk.Label(self.page_container, text="Journaux d'activité", 
                            style="Heading.TLabel")
        page_title.pack(anchor=tk.W, pady=(0, 20))
        
        # Cadre pour les journaux
        log_frame = ttk.Frame(self.page_container, style="Card.TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=1)
        
        # Zone de texte pour les journaux
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, bg=CARD_BG, fg=TEXT_COLOR,
                             insertbackground=TEXT_COLOR, relief="flat", borderwidth=0,
                             font=self.font_normal)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Charger les journaux
        self.load_logs()
    
    def load_logs(self):
        """Charger et afficher les journaux"""
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            self.log_text.insert(tk.END, "Aucun fichier journal trouvé.")
            return
        
        # Trouver le fichier journal le plus récent
        log_files = [f for f in os.listdir(log_dir) if f.startswith('imprimante_api_')]
        
        if not log_files:
            self.log_text.insert(tk.END, "Aucun fichier journal trouvé.")
            return
        
        # Trier par date (le plus récent en premier)
        log_files.sort(reverse=True)
        latest_log = os.path.join(log_dir, log_files[0])
        
        try:
            with open(latest_log, 'r', encoding='utf-8') as file:
                log_content = file.read()
                self.log_text.insert(tk.END, log_content)
                self.log_text.see(tk.END)  # Défiler jusqu'à la fin
        except Exception as e:
            self.log_text.insert(tk.END, f"Erreur lors de la lecture du journal: {e}")
    
    def create_stat_card(self, parent, title, value, position):
        """Créer une carte de statistique"""
        # Calculer la largeur et la position
        card_width = 200
        card_height = 120
        margin = 15
        x = position * (card_width + margin)
        
        # Créer un cadre pour la carte
        card = ttk.Frame(parent, style="Card.TFrame", width=card_width, height=card_height)
        card.pack(side=tk.LEFT, padx=(0 if position == 0 else margin, 0))
        card.pack_propagate(False)  # Garder la taille fixe
        
        # Titre de la carte
        title_label = ttk.Label(card, text=title, style="Card.TLabel", font=self.font_normal)
        title_label.pack(anchor=tk.NW, padx=15, pady=(15, 5))
        
        # Valeur
        if isinstance(value, int):
            value_text = str(value)
        else:
            value_text = value
            
        value_label = ttk.Label(card, text=value_text, style="Card.TLabel", 
                             font=self.font_heading)
        value_label.pack(anchor=tk.NW, padx=15)
        
        return card
    
    def create_action_card(self, parent, title, description, command, position):
        """Créer une carte d'action"""
        # Calculer la largeur et la position
        card_width = 200
        card_height = 150
        margin = 15
        x = position * (card_width + margin)
        
        # Créer un cadre pour la carte
        card = ttk.Frame(parent, style="Card.TFrame", width=card_width, height=card_height)
        card.pack(side=tk.LEFT, padx=(0 if position == 0 else margin, 0))
        card.pack_propagate(False)  # Garder la taille fixe
        
        # Titre de la carte
        title_label = ttk.Label(card, text=title, style="Card.TLabel", 
                             font=self.font_subheading)
        title_label.pack(anchor=tk.NW, padx=15, pady=(15, 5))
        
        # Description
        desc_label = ttk.Label(card, text=description, style="Card.TLabel", 
                            font=self.font_small, wraplength=170)
        desc_label.pack(anchor=tk.NW, padx=15, pady=(0, 10), fill=tk.X)
        
        # Bouton d'action
        action_btn = ttk.Button(card, text="Exécuter", command=command, style="TButton")
        action_btn.pack(anchor=tk.SW, padx=15, pady=15)
        
        return card
    
    def on_resize(self, event):
        """Gérer le redimensionnement de la fenêtre"""
        # Mettre à jour l'interface si nécessaire lors d'un redimensionnement
        pass
    
    def refresh_printers(self):
        """Récupérer la liste des imprimantes disponibles"""
        try:
            self.printers = get_printers()
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de récupérer les imprimantes: {e}")
            return False
    
    def test_default_printer(self):
        """Tester l'imprimante par défaut"""
        if config.get('default_printer_name') is None:
            messagebox.showwarning("Aucune imprimante", 
                                 "Aucune imprimante par défaut définie.\n"
                                 "Veuillez d'abord définir une imprimante par défaut.")
            return
        
        self.test_printer_by_name(config.get('default_printer_name'))
    
    def test_selected_printer(self):
        """Tester l'imprimante sélectionnée"""
        if self.selected_printer_id is None:
            messagebox.showwarning("Aucune sélection", 
                                 "Veuillez sélectionner une imprimante à tester.")
            return
        
        # Rechercher le nom de l'imprimante
        printer_name = None
        for printer in self.printers:
            if printer['id'] == self.selected_printer_id:
                printer_name = printer['name']
                break
        
        if printer_name:
            self.test_printer_by_name(printer_name)
        else:
            messagebox.showerror("Erreur", "Imprimante introuvable.")
    
    def test_printer_by_name(self, printer_name):
        """Tester l'imprimante par son nom - MISE À JOUR ASCII"""
        # Afficher un dialogue de progression
        progress_window = tk.Toplevel(self)
        progress_window.title("Impression ASCII en cours")
        progress_window.geometry("350x120")
        progress_window.configure(bg=DARK_BG)
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Centrer la fenêtre
        progress_window.update_idletasks()
        width = progress_window.winfo_width()
        height = progress_window.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        progress_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu de la fenêtre
        label = ttk.Label(progress_window, text=f"Impression ASCII sur {printer_name}...", 
                        style="TLabel")
        label.pack(pady=(20, 5))
        
        ascii_label = ttk.Label(progress_window, text="Conversion française automatique", 
                              style="Secondary.TLabel", font=self.font_small)
        ascii_label.pack(pady=(0, 10))
        
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=30)
        progress.start()
        
        # Effectuer l'impression dans un thread séparé
        def print_test_thread():
            success = print_test(printer_name)
            
            # Fermer la fenêtre de progression
            self.after(0, progress_window.destroy)
            
            # Afficher le résultat
            if success:
                self.after(0, lambda: messagebox.showinfo("Test ASCII réussi", 
                                                       f"Test d'impression ASCII envoyé à {printer_name}.\n"
                                                       f"Conversion française appliquée automatiquement.\n"
                                                       f"Vérifiez que les accents sont correctement convertis."))
            else:
                self.after(0, lambda: messagebox.showerror("Erreur", 
                                                        f"Échec du test d'impression sur {printer_name}."))
        
        threading.Thread(target=print_test_thread).start()
    
    def set_default_printer(self):
        """Définir l'imprimante sélectionnée comme imprimante par défaut - CORRIGÉ ASCII"""
        if self.selected_printer_id is None:
            messagebox.showwarning("Aucune sélection", 
                                 "Veuillez sélectionner une imprimante à définir par défaut.")
            return
        
        # Rechercher le nom et la largeur de l'imprimante
        printer_name = None
        printer_width = "58mm"  # Valeur par défaut
        printer_encoding = "ascii"  # MODIFIÉ: ASCII par défaut maintenant
        
        for printer in self.printers:
            if printer['id'] == self.selected_printer_id:
                printer_name = printer['name']
                printer_width = printer.get('width', "58mm")  # Récupérer la largeur détectée
                printer_encoding = printer.get('encoding', "ascii")  # MODIFIÉ: ASCII par défaut
                break
        
        if not printer_name:
            messagebox.showerror("Erreur", "Imprimante introuvable.")
            return
        
        config['default_printer_id'] = self.selected_printer_id
        config['default_printer_name'] = printer_name
        config['default_printer_width'] = printer_width  # Enregistrer la largeur
        
        save_config()
        
        # Mettre à jour la valeur dans l'interface des paramètres
        if hasattr(self, 'width_var'):
            self.width_var.set(printer_width)
        
        # Mettre à jour l'interface
        if self.current_page.get() == "printers":
            self.update_printer_list()
        elif self.current_page.get() == "dashboard":
            # Recréer le tableau de bord pour montrer l'imprimante par défaut mise à jour
            self.show_dashboard()
        
        # MODIFIÉ: Message avec ASCII par défaut
        messagebox.showinfo("Imprimante par défaut", 
                          f"{printer_name} définie comme imprimante par défaut.\n"
                          f"Largeur détectée: {printer_width}\n"
                          f"Encodage: {printer_encoding} (ASCII universel)\n"
                          f"Conversion française automatique activée.")
    
    def apply_port_setting(self):
        """Appliquer le changement de port"""
        try:
            new_port = int(self.port_var.get())
            if new_port < 1024 or new_port > 65535:
                messagebox.showerror("Erreur", "Le port doit être compris entre 1024 et 65535.")
                return
            
            config['port'] = new_port
            save_config()
            
            # Mettre à jour l'URL affichée
            api_url = f"http://localhost:{new_port}"
            self.url_var.set(api_url)
            
            messagebox.showinfo("Port modifié", 
                             f"Le port a été changé pour {new_port}.\n"
                             f"Veuillez redémarrer l'application pour appliquer ce changement.")
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un numéro de port valide.")
    
    def save_all_settings(self):
        """Enregistrer tous les paramètres - MISE À JOUR ASCII"""
        # Sauvegarder l'encodage (même si ASCII est forcé par défaut)
        config['default_encoding'] = self.encoding_var.get()
        
        # NOUVEAU: S'assurer que force_ascii_for_all est activé si ASCII est sélectionné
        if self.encoding_var.get() == 'ascii':
            config['force_ascii_for_all'] = True
            config['pos58_encoding'] = 'ascii'
            config['standard_encoding'] = 'ascii'
        
        save_config()
        messagebox.showinfo("Paramètres enregistrés", 
                          "Tous les paramètres ont été enregistrés.\n"
                          "ASCII universel avec conversion française activé.")
    
    def open_browser(self):
        """Ouvrir l'API dans le navigateur"""
        api_url = f"http://localhost:{config.get('port', 5789)}"
        webbrowser.open(api_url)

def launch_config_gui():
    """Lance l'interface graphique moderne avec support ASCII"""
    app = ModernApp()
    
    # Centrer la fenêtre
    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f"+{x}+{y}")
    
    app.mainloop()

if __name__ == "__main__":
    launch_config_gui()