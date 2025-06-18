# Add this to your existing ModsTab class in gui/tabs/mods.py

def create_toolbar(self):
    """Create the toolbar with mod management actions"""
    theme = self.thememanager.get_current_theme()
    
    # Toolbar frame
    toolbar_frame = tk.Frame(self.tab_frame, bg=theme.get('bg_secondary', '#f8f9fa'), height=50)
    toolbar_frame.pack(fill='x', padx=5, pady=(5, 0))
    toolbar_frame.pack_propagate(False)
    
    # Left side buttons
    left_frame = tk.Frame(toolbar_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    left_frame.pack(side='left', fill='y', pady=8)
    
    # Add mod button
    self.add_btn = tk.Button(
        left_frame,
        text="➕ Add Mods",
        font=('Segoe UI', 10, 'bold'),
        bg='#28a745',
        fg='white',
        padx=15,
        pady=6,
        relief='flat',
        cursor='hand2',
        command=self.add_mods
    )
    self.add_btn.pack(side='left', padx=(0, 8))
    
    # Refresh button
    self.refresh_btn = tk.Button(
        left_frame,
        text="🔄 Refresh",
        font=('Segoe UI', 10),
        bg=theme.get('accent', '#007bff'),
        fg='white',
        padx=12,
        pady=6,
        relief='flat',
        cursor='hand2',
        command=self.refresh_mods
    )
    self.refresh_btn.pack(side='left', padx=(0, 8))
    
    # Bulk actions frame (initially hidden)
    self.bulk_frame = tk.Frame(left_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    self.bulk_frame.pack(side='left', padx=(8, 0))
    
    # Selection count label
    self.selection_label = tk.Label(
        self.bulk_frame,
        text="0 selected",
        font=('Segoe UI', 9),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_secondary', '#6c757d')
    )
    self.selection_label.pack(side='left', padx=(0, 8))
    
    # Bulk enable button
    self.bulk_enable_btn = tk.Button(
        self.bulk_frame,
        text="Enable Selected",
        font=('Segoe UI', 9),
        bg='#28a745',
        fg='white',
        padx=10,
        pady=4,
        relief='flat',
        cursor='hand2',
        command=self.bulk_enable
    )
    self.bulk_enable_btn.pack(side='left', padx=(0, 5))
    
    # Bulk disable button
    self.bulk_disable_btn = tk.Button(
        self.bulk_frame,
        text="Disable Selected",
        font=('Segoe UI', 9),
        bg='#dc3545',
        fg='white',
        padx=10,
        pady=4,
        relief='flat',
        cursor='hand2',
        command=self.bulk_disable
    )
    self.bulk_disable_btn.pack(side='left', padx=(0, 5))
    
    # Bulk remove button
    self.bulk_remove_btn = tk.Button(
        self.bulk_frame,
        text="Remove Selected",
        font=('Segoe UI', 9),
        bg='#6c757d',
        fg='white',
        padx=10,
        pady=4,
        relief='flat',
        cursor='hand2',
        command=self.bulk_remove
    )
    self.bulk_remove_btn.pack(side='left')
    
    # Center section - Search and filters
    center_frame = tk.Frame(toolbar_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    center_frame.pack(side='left', fill='both', expand=True, padx=20, pady=8)
    
    # Search frame
    search_frame = tk.Frame(center_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    search_frame.pack(fill='x')
    
    # Search icon and entry
    tk.Label(
        search_frame,
        text="🔍",
        font=('Segoe UI', 12),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_secondary', '#6c757d')
    ).pack(side='left', padx=(0, 5))
    
    self.search_entry = tk.Entry(
        search_frame,
        textvariable=self.search_var,
        font=('Segoe UI', 10),
        bg='white',
        fg=theme.get('text_primary', 'black'),
        relief='solid',
        bd=1,
        width=30
    )
    self.search_entry.pack(side='left', fill='x', expand=True)
    self.search_entry.bind('<KeyRelease>', self.on_search_changed)
    
    # Clear search button
    self.clear_search_btn = tk.Button(
        search_frame,
        text="✕",
        font=('Segoe UI', 10),
        bg='#6c757d',
        fg='white',
        padx=8,
        pady=1,
        relief='flat',
        cursor='hand2',
        command=self.clear_search
    )
    self.clear_search_btn.pack(side='left', padx=(5, 0))
    
    # Right side controls
    right_frame = tk.Frame(toolbar_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    right_frame.pack(side='right', fill='y', pady=8)
    
    # View mode toggle
    view_frame = tk.Frame(right_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    view_frame.pack(side='right', padx=(0, 10))
    
    tk.Label(
        view_frame,
        text="View:",
        font=('Segoe UI', 9),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    ).pack(side='left', padx=(0, 5))
    
    # Grid view button
    self.grid_view_btn = tk.Button(
        view_frame,
        text="⊞",
        font=('Segoe UI', 12),
        bg=theme.get('accent', '#007bff'),
        fg='white',
        padx=8,
        pady=2,
        relief='flat',
        cursor='hand2',
        command=lambda: self.set_view_mode('grid')
    )
    self.grid_view_btn.pack(side='left', padx=(0, 2))
    
    # List view button
    self.list_view_btn = tk.Button(
        view_frame,
        text="☰",
        font=('Segoe UI', 12),
        bg='#6c757d',
        fg='white',
        padx=8,
        pady=2,
        relief='flat',
        cursor='hand2',
        command=lambda: self.set_view_mode('list')
    )
    self.list_view_btn.pack(side='left')
    
    # Sort options
    sort_frame = tk.Frame(right_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
    sort_frame.pack(side='right', padx=(0, 10))
    
    tk.Label(
        sort_frame,
        text="Sort:",
        font=('Segoe UI', 9),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    ).pack(side='left', padx=(0, 5))
    
    self.sort_var = tk.StringVar(value="name")
    sort_combo = ttk.Combobox(
        sort_frame,
        textvariable=self.sort_var,
        values=["name", "author", "size", "date"],
        state="readonly",
        width=8,
        font=('Segoe UI', 9)
    )
    sort_combo.pack(side='left')
    sort_combo.bind('<<ComboboxSelected>>', self.on_sort_changed)
    
    # Sort direction button
    self.sort_dir_btn = tk.Button(
        sort_frame,
        text="↑",
        font=('Segoe UI', 12),
        bg='#6c757d',
        fg='white',
        padx=6,
        pady=2,
        relief='flat',
        cursor='hand2',
        command=self.toggle_sort_direction
    )
    self.sort_dir_btn.pack(side='left', padx=(2, 0))
    
    # Update bulk actions visibility
    self.update_bulk_actions_visibility()

def create_sidebar(self):
    """Create the sidebar with filters and categories"""
    theme = self.thememanager.get_current_theme()
    
    # Sidebar frame
    sidebar_frame = tk.Frame(
        self.main_frame,
        bg=theme.get('bg_secondary', '#f8f9fa'),
        width=250,
        relief='solid',
        bd=1
    )
    sidebar_frame.pack(side='left', fill='y', padx=(5, 0), pady=5)
    sidebar_frame.pack_propagate(False)
    
    # Sidebar content with scroll
    sidebar_canvas = tk.Canvas(
        sidebar_frame,
        bg=theme.get('bg_secondary', '#f8f9fa'),
        highlightthickness=0
    )
    sidebar_scrollbar = ttk.Scrollbar(
        sidebar_frame,
        orient='vertical',
        command=sidebar_canvas.yview
    )
    sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
    
    sidebar_content = tk.Frame(sidebar_canvas, bg=theme.get('bg_secondary', '#f8f9fa'))
    sidebar_window = sidebar_canvas.create_window((0, 0), window=sidebar_content, anchor='nw')
    
    sidebar_canvas.pack(side='left', fill='both', expand=True, padx=5, pady=5)
    sidebar_scrollbar.pack(side='right', fill='y')
    
    # Categories section
    self.create_categories_section(sidebar_content, theme)
    
    # Status filters section
    self.create_status_filters_section(sidebar_content, theme)
    
    # Mod loader filters section  
    self.create_loader_filters_section(sidebar_content, theme)
    
    # Quick actions section
    self.create_quick_actions_section(sidebar_content, theme)
    
    # Bind scroll events
    def configure_sidebar_scroll(event):
        sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox('all'))
        sidebar_canvas.itemconfig(sidebar_window, width=event.width-10)
    
    sidebar_content.bind('<Configure>', configure_sidebar_scroll)
    sidebar_canvas.bind('<MouseWheel>', lambda e: sidebar_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

def create_categories_section(self, parent, theme):
    """Create categories filter section"""
    # Categories header
    categories_frame = tk.LabelFrame(
        parent,
        text="Categories",
        font=('Segoe UI', 10, 'bold'),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    )
    categories_frame.pack(fill='x', pady=(0, 10))
    
    # All mods
    self.category_vars = {}
    self.category_vars['all'] = tk.BooleanVar(value=True)
    
    all_cb = tk.Checkbutton(
        categories_frame,
        text="All Mods",
        variable=self.category_vars['all'],
        font=('Segoe UI', 9, 'bold'),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black'),
        command=self.on_category_filter_changed
    )
    all_cb.pack(anchor='w', padx=5, pady=2)
    
    # Common categories
    categories = ['Favorites', 'Enabled', 'Disabled', 'Updates Available', 'Essential']
    for category in categories:
        var = tk.BooleanVar()
        self.category_vars[category.lower().replace(' ', '_')] = var
        
        cb = tk.Checkbutton(
            categories_frame,
            text=category,
            variable=var,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', '#f8f9fa'),
            fg=theme.get('text_primary', 'black'),
            command=self.on_category_filter_changed
        )
        cb.pack(anchor='w', padx=5, pady=1)

def create_status_filters_section(self, parent, theme):
    """Create status filters section"""
    status_frame = tk.LabelFrame(
        parent,
        text="Status",
        font=('Segoe UI', 10, 'bold'),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    )
    status_frame.pack(fill='x', pady=(0, 10))
    
    # Status checkboxes
    self.status_vars = {}
    statuses = [
        ('Show Enabled', 'enabled', True),
        ('Show Disabled', 'disabled', True),
        ('Show Favorites', 'favorites', False),
        ('Show Essential', 'essential', False)
    ]
    
    for text, key, default in statuses:
        var = tk.BooleanVar(value=default)
        self.status_vars[key] = var
        
        cb = tk.Checkbutton(
            status_frame,
            text=text,
            variable=var,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', '#f8f9fa'),
            fg=theme.get('text_primary', 'black'),
            command=self.on_status_filter_changed
        )
        cb.pack(anchor='w', padx=5, pady=1)

def create_loader_filters_section(self, parent, theme):
    """Create mod loader filters section"""
    loader_frame = tk.LabelFrame(
        parent,
        text="Mod Loaders",
        font=('Segoe UI', 10, 'bold'),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    )
    loader_frame.pack(fill='x', pady=(0, 10))
    
    # Loader checkboxes
    self.loader_vars = {}
    loaders = ['Forge', 'Fabric', 'Quilt', 'Vanilla']
    
    for loader in loaders:
        var = tk.BooleanVar(value=True)
        self.loader_vars[loader.lower()] = var
        
        cb = tk.Checkbutton(
            loader_frame,
            text=loader,
            variable=var,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', '#f8f9fa'),
            fg=theme.get('text_primary', 'black'),
            command=self.on_loader_filter_changed
        )
        cb.pack(anchor='w', padx=5, pady=1)

def create_quick_actions_section(self, parent, theme):
    """Create quick actions section"""
    actions_frame = tk.LabelFrame(
        parent,
        text="Quick Actions",
        font=('Segoe UI', 10, 'bold'),
        bg=theme.get('bg_secondary', '#f8f9fa'),
        fg=theme.get('text_primary', 'black')
    )
    actions_frame.pack(fill='x', pady=(0, 10))
    
    # Action buttons
    actions = [
        ("Enable All", self.enable_all_mods),
        ("Disable All", self.disable_all_mods),
        ("Check Updates", self.check_for_updates),
        ("Backup Mods", self.backup_mods),
        ("Open Mods Folder", self.open_mods_folder)
    ]
    
    for text, command in actions:
        btn = tk.Button(
            actions_frame,
            text=text,
            font=('Segoe UI', 9),
            bg=theme.get('accent', '#007bff'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=command
        )
        btn.pack(fill='x', padx=5, pady=2)
        
    
