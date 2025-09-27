const { useState, useEffect } = React;

const CATEGORY_ORDER = [
  'Appetizer',
  'Nigiri',
  'Maki Rolls',
  'Speciality Rolls',
];

const NAV_OPTIONS = [
  { label: 'Menu', key: 'menu' },
  { label: 'Runbook', key: 'runbook' },
  { label: 'Shopping Items', key: 'shopping_items' },
  { label: 'Shopping List', key: 'shopping_list' },
  { label: 'Recipes', key: 'recipes' },
];

const COLORS = {
  bg: '#1a1a1a', // Softer dark background - easier on eyes
  highlight: '#00D4AA', // Solana teal/aqua green
  white: '#ffffff', // Pure white text
  card: '#2a2a2a', // Lighter card background
  border: '#3a3a3a', // Subtle borders
  grey: '#b0b8c1', // Light grey for secondary text
  green: '#00D4AA', // Solana green for shopping mode
  purple: '#9945FF', // Solana purple for accents
  blue: '#1E3A8A', // Dark blue for majority of boxes
  teal: '#00D4AA', // Teal for highlights
};

function getDescription(item) {
  if (item.category && item.category.toLowerCase().includes('nigiri')) {
    let fish = item.name.split(' ')[0];
    let topping = '';
    if (item.ingredients && item.ingredients.length > 1) {
      topping = item.ingredients.slice(1).join(', ');
    }
    if (item.name.toLowerCase().includes('seared')) {
      fish = 'Seared ' + fish;
    }
    if (topping) {
      return `${fish} topped w/ ${topping}`;
    } else {
      return `${fish}`;
    }
  }
  if (item.category && item.category.toLowerCase().includes('roll')) {
    let main = item.ingredients && item.ingredients.length > 0 ? item.ingredients[0] : '';
    let others = item.ingredients && item.ingredients.length > 1 ? item.ingredients.slice(1).join(', ') : '';
    let topping = '';
    if (item["Ingrediant on top"]) {
      topping = item["Ingrediant on top"];
    }
    let desc = main;
    if (others) desc += ` and ${others}`;
    if (topping) desc += ` topped w/ ${topping}`;
    return desc;
  }
  return item.ingredients ? item.ingredients.join(', ') : '';
}

function categorizeIngredients(ingredients) {
  const groups = { Fish: [], Dairy: [], Vegetables: [], Other: [] };
  Object.values(ingredients).forEach(arr => {
    arr.forEach(ing => {
      const cat = (ing.category || '').toLowerCase();
      if (cat.includes('fish') || cat.includes('seafood') || cat.includes('tuna') || cat.includes('salmon')) {
        groups.Fish.push(ing);
      } else if (cat.includes('dairy')) {
        groups.Dairy.push(ing);
      } else if (cat.includes('vegetable') || cat.includes('veggie')) {
        groups.Vegetables.push(ing);
      } else {
        groups.Other.push(ing);
      }
    });
  });
  return groups;
}

// Helper: Get all ingredients for selected menu items
function getCartIngredients(cart, ingredientsMaster) {
  // Build a map of ingredient name -> ingredient object (for category lookup)
  const ingredientMap = {};
  Object.values(ingredientsMaster).flat().forEach(ing => {
    ingredientMap[ing.name.toLowerCase()] = ing;
  });
  // Gather all ingredients from cart
  let allIngredients = [];
  cart.forEach(item => {
    // Combine inside and on top
    const inside = (item.ingredients_inside || []).map(i => i.trim()).filter(Boolean);
    const onTop = (item.ingredients_on_top || []).map(i => i.trim()).filter(Boolean);
    allIngredients.push(...inside, ...onTop);
  });
  // Deduplicate (case-insensitive)
  const uniqueNames = Array.from(new Set(allIngredients.map(i => i.toLowerCase())));
  // Map to ingredient objects (with fallback if not found)
  return uniqueNames.map(name => ingredientMap[name] || { name });
}

// Helper: Count menu items in cart
function getCartSummary(cart) {
  return cart.map(i => ({ ...i, count: i.quantity }));
}

// Helper: get image path for menu item
function getMenuItemImage(item) {
  // Only use .jpeg, all lowercase, underscores for spaces
  const category = (item.category || '').toLowerCase().replace(/\s+/g, '_');
  const name = (item.name || '').toLowerCase().replace(/\s+/g, '_');
  return `pictures/${category}_${name}.jpeg`;
}

// 1. Helper to get all needed ingredients for cart items, grouped by category, summed quantity
function getCartIngredientsSummary(cart, ingredientsMaster) {
  // Build a map of ingredient name -> { ...ingredient, totalQty }
  const ingredientMap = {};
  Object.values(ingredientsMaster).flat().forEach(ing => {
    ingredientMap[ing.name.toLowerCase()] = { ...ing, totalQty: 0 };
  });
  
  // Check if cart has any rolls (for smart ingredient logic)
  const hasRolls = cart.some(item => 
    item.category === 'Maki Rolls' || item.category === 'Speciality Rolls'
  );
  
  // Add smart ingredients if rolls are present
  if (hasRolls) {
    const smartIngredients = ['Rice', 'Soy Sauce', 'Wasabi'];
    smartIngredients.forEach(smartName => {
      const key = smartName.toLowerCase();
      if (ingredientMap[key]) {
        ingredientMap[key].totalQty = 1; // Always add 1 of each smart ingredient
      }
    });
  }
  
  // For each cart item, add up ingredient quantities
  cart.forEach(item => {
    const qty = item.quantity || 1;
    // Use both ingredients_inside and ingredients_on_top
    const inside = (item.ingredients_inside || []).map(i => i.trim()).filter(Boolean);
    const onTop = (item.ingredients_on_top || []).map(i => i.trim()).filter(Boolean);
    [...inside, ...onTop].forEach(ingName => {
      const key = ingName.toLowerCase();
      if (ingredientMap[key]) {
        ingredientMap[key].totalQty += qty;
      } else {
        // Fallback for missing ingredient in master list
        ingredientMap[key] = { name: ingName, category: 'Other', store: '', totalQty: qty };
      }
    });
  });
  
  // Group by category
  const grouped = {};
  Object.values(ingredientMap).forEach(ing => {
    if (ing.totalQty > 0) {
      const cat = ing.category || 'Other';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(ing);
    }
  });
  // Sort categories and ingredients
  const sortedCats = Object.keys(grouped).sort();
  sortedCats.forEach(cat => {
    grouped[cat].sort((a, b) => a.name.localeCompare(b.name));
  });
  return { grouped, sortedCats };
}

function App() {
  const [menu, setMenu] = useState({});
  const [ingredients, setIngredients] = useState({});
  const [runbook, setRunbook] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openCategories, setOpenCategories] = useState({});
  // 1. Update cart state to store {item, quantity}
  const [cart, setCart] = useState([]); // [{...item, quantity: N}]
  const [navOpen, setNavOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('menu');
  // Remove shoppingMode state
  // const [shoppingMode, setShoppingMode] = useState(false);
  const [runbookDone, setRunbookDone] = useState([]); // array of indices
  const [hoveredRunbook, setHoveredRunbook] = useState(null); // index of hovered row
  const [selectedCategories, setSelectedCategories] = useState(new Set()); // Track selected category filters
  const [runbookFilter, setRunbookFilter] = useState('beginner'); // 'beginner' or 'advanced'
  const [selectedRunbookItem, setSelectedRunbookItem] = useState(null); // Selected item for tips panel
  const [menuFilter, setMenuFilter] = useState('all'); // all, top-ranked, salmon, tuna, veggie

  useEffect(() => {
    // Fetch data from API endpoints
    Promise.all([
      fetch('http://localhost:5001/api/menu'),
      fetch('http://localhost:5001/api/ingredients'),
      fetch('http://localhost:5001/api/runbook')
    ])
      .then(responses => Promise.all(responses.map(res => res.json())))
      .then(([menuData, ingredientsData, runbookData]) => {
        setMenu(menuData || {});
        setIngredients(ingredientsData || {});
        setRunbook(runbookData || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('API Error:', err);
        setError('Failed to load menu data from API.');
        setLoading(false);
      });
  }, []);

  const toggleCategory = (cat) => {
    setOpenCategories((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const toggleCategoryFilter = (cat) => {
    setSelectedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cat)) {
        newSet.delete(cat);
      } else {
        newSet.add(cat);
      }
      
      // Auto-expand/collapse categories based on filter selection
      if (newSet.size > 0) {
        // When filters are selected, expand all filtered categories
        const newOpenCategories = {};
        newSet.forEach(selectedCat => {
          newOpenCategories[selectedCat] = true;
        });
        setOpenCategories(newOpenCategories);
      } else {
        // When no filters are selected, collapse all categories
        setOpenCategories({});
      }
      
      return newSet;
    });
  };

  // 2. Helper to get cart item by name/category
  const getCartItem = (item) => cart.find(i => i.name === item.name && i.category === item.category);
  const isInCart = (item) => !!getCartItem(item);

  // 3. Add/update/remove item in cart
  const addToCart = (item) => {
    setCart(prev => {
      const found = prev.find(i => i.name === item.name && i.category === item.category);
      if (found) {
        // Already in cart, increase quantity up to 5
        return prev.map(i => i.name === item.name && i.category === item.category ? { ...i, quantity: Math.min(i.quantity + 1, 5) } : i);
      } else {
        return [...prev, { ...item, quantity: 1 }];
      }
    });
  };
  const removeFromCart = (item) => {
    setCart(prev => prev.filter(i => !(i.name === item.name && i.category === item.category)));
  };
  const setCartQuantity = (item, qty) => {
    if (qty < 1) return removeFromCart(item);
    setCart(prev => prev.map(i => i.name === item.name && i.category === item.category ? { ...i, quantity: Math.min(Math.max(qty, 1), 5) } : i));
  };

  // 4. Update getCartSummary to use quantity
  function getCartSummary(cart) {
    return cart.map(i => ({ ...i, count: i.quantity }));
  }

  const orderedCategories = CATEGORY_ORDER.filter(cat => menu[cat]);
  const filteredCategories = selectedCategories.size > 0 
    ? orderedCategories.filter(cat => selectedCategories.has(cat))
    : orderedCategories;

  // Cart toggle logic
  // const isInCart = (item) => cart.some(i => i.name === item.name && i.category === item.category);
  // const toggleCart = (item) => {
  //   setCart((prev) => {
  //     if (isInCart(item)) {
  //       return prev.filter(i => !(i.name === item.name && i.category === item.category));
  //     } else {
  //       return [...prev, item];
  //     }
  //   });
  // };

  // Shopping cart ingredient categorization (future: link to rolls)
  const categorizedCart = categorizeIngredients({
    ...Object.fromEntries(cart.map(item => [item.name, [{
      category: item.category,
      name: item.name,
    }]])),
  });

  // All ingredients categorized for Shopping Items
  const categorizedIngredients = categorizeIngredients(ingredients);

  // Sidebar nav click handler
  const handleNavClick = (key) => {
    setActiveNav(key);
    setNavOpen(false);
  };

  // Main content margin for cart, tips panel, and recipe modal
  const mainContentStyle = {
    marginRight: (activeNav === 'menu' && cart.length > 0) ? 320 : 
                 (activeNav === 'runbook' && selectedRunbookItem) ? 300 :
                 (activeNav === 'recipes' && selectedRecipe) ? 400 : 0,
    transition: 'margin-right 0.3s',
  };

  // Table columns for Shopping Items
  const ingredientColumns = [
    { label: 'Category', key: 'category' },
    { label: 'Name', key: 'name' },
    { label: 'Store', key: 'store' },
    { label: 'Cost', key: 'cost' },
    { label: 'Quantity', key: 'quantity' },
    { label: 'Unit Cost', key: 'unit_cost' },
  ];

  // Shopping Items filters and sort state
  const [shoppingCategory, setShoppingCategory] = useState('');
  const [shoppingStore, setShoppingStore] = useState('');
  const [shoppingName, setShoppingName] = useState('');
  const [shoppingSort, setShoppingSort] = useState({ key: 'name', dir: 'asc' });

  // Shopping List state
  const [shoppingListSort, setShoppingListSort] = useState({ key: 'store', dir: 'asc' });
  const [alreadyHaveIngredients, setAlreadyHaveIngredients] = useState(new Set());

  // Recipes state
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [recipes, setRecipes] = useState([
    {
      id: 1,
      name: 'Nikiri Sauce',
      category: 'Sauce',
      description: 'Traditional Japanese sauce for sushi and sashimi. A complex, umami-rich sauce that enhances the natural flavors of fish.',
      ingredients: [
        { name: 'Normal soy', amount: '3 oz' },
        { name: 'Sweet soy', amount: '2 oz' },
        { name: 'Mirin', amount: '2 oz' },
        { name: 'Sake', amount: '2 oz' },
        { name: 'Konbu', amount: '1 piece' },
        { name: 'Bonito flakes', amount: '1 bag' }
      ],
      instructions: 'Combine all ingredients and simmer until reduced by half. Strain and store.',
      storage: 'Can store up to 1 month',
      prepTime: '30 minutes',
      difficulty: 'Intermediate'
    },
    {
      id: 2,
      name: 'Yellowtail Yuzu',
      category: 'Preparation',
      description: 'Delicate preparation featuring thinly sliced sashimi-grade yellowtail with fresh jalapeño, garlic, and yuzu soy sauce',
      ingredients: [
        { name: 'Yellowtail', amount: '8 oz' },
        { name: 'Jalapeño', amount: '1 pepper' },
        { name: 'Garlic', amount: '2 cloves' },
        { name: 'Yuzu juice', amount: '2 tbsp' },
        { name: 'Soy sauce', amount: '1 tbsp' },
        { name: 'Cilantro', amount: '2 tbsp' }
      ],
      instructions: 'Thinly slice yellowtail, arrange on plate, top with jalapeño, press against garlic, finish with yuzu soy sauce, garnish with cilantro',
      storage: 'Serve immediately',
      prepTime: '15 minutes',
      difficulty: 'Easy'
    }
  ]);
  const [recipeFilter, setRecipeFilter] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  // Recipe filtering logic
  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = !recipeFilter || 
      recipe.name.toLowerCase().includes(recipeFilter.toLowerCase()) ||
      recipe.description.toLowerCase().includes(recipeFilter.toLowerCase());
    const matchesCategory = !selectedCategory || recipe.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const recipeCategories = Array.from(new Set(recipes.map(r => r.category)));

  // Already have ingredient functions
  const markAsAlreadyHave = (ingredient) => {
    const key = `${ingredient.name}-${ingredient.store}-${ingredient.category}`;
    setAlreadyHaveIngredients(prev => new Set([...prev, key]));
  };

  const unmarkAsAlreadyHave = (ingredient) => {
    const key = `${ingredient.name}-${ingredient.store}-${ingredient.category}`;
    setAlreadyHaveIngredients(prev => {
      const newSet = new Set(prev);
      newSet.delete(key);
      return newSet;
    });
  };

  const isAlreadyHave = (ingredient) => {
    const key = `${ingredient.name}-${ingredient.store}-${ingredient.category}`;
    return alreadyHaveIngredients.has(key);
  };

  // Get all ingredients flat
  const allIngredients = Object.values(ingredients).flat();
  // Unique categories and stores for dropdowns
  const uniqueCategories = Array.from(new Set(allIngredients.map(i => i.category))).filter(Boolean);
  const uniqueStores = Array.from(new Set(allIngredients.map(i => i.store))).filter(Boolean);

  // Filter and sort logic
  let filteredIngredients = allIngredients.filter(ing =>
    (!shoppingCategory || ing.category === shoppingCategory) &&
    (!shoppingStore || ing.store === shoppingStore) &&
    (!shoppingName || (ing.name && ing.name.toLowerCase().includes(shoppingName.toLowerCase())) || (ing.shopping_cart_name && ing.shopping_cart_name.toLowerCase().includes(shoppingName.toLowerCase())))
  );
  if (shoppingSort.key) {
    filteredIngredients = filteredIngredients.slice().sort((a, b) => {
      let av = a[shoppingSort.key] || '';
      let bv = b[shoppingSort.key] || '';
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return shoppingSort.dir === 'asc' ? -1 : 1;
      if (av > bv) return shoppingSort.dir === 'asc' ? 1 : -1;
      return 0;
    });
  }

  // Get cart-based ingredients for shopping list
  const cartIngredientsData = getCartIngredientsSummary(cart, ingredients);
  const cartIngredientsList = Object.values(cartIngredientsData.grouped).flat();

  // Shopping List filtering and sorting logic (based on cart ingredients)
  let filteredShoppingList = cartIngredientsList;
  
  // Separate ingredients into "need to buy" and "already have"
  let needToBuyIngredients = filteredShoppingList.filter(ing => !isAlreadyHave(ing));
  let alreadyHaveList = filteredShoppingList.filter(ing => isAlreadyHave(ing));
  
  // Apply sorting to both lists
  if (shoppingListSort.key) {
    const sortFunction = (a, b) => {
      let av = a[shoppingListSort.key] || '';
      let bv = b[shoppingListSort.key] || '';
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return shoppingListSort.dir === 'asc' ? -1 : 1;
      if (av > bv) return shoppingListSort.dir === 'asc' ? 1 : -1;
      return 0;
    };
    
    needToBuyIngredients = needToBuyIngredients.slice().sort(sortFunction);
    alreadyHaveList = alreadyHaveList.slice().sort(sortFunction);
  }

  // Group shopping list by category for iPhone-optimized export
  const groupedShoppingList = {};
  filteredShoppingList.forEach(ing => {
    const category = ing.category || 'Other';
    if (!groupedShoppingList[category]) {
      groupedShoppingList[category] = [];
    }
    groupedShoppingList[category].push(ing);
  });

  function getTimeToShowTime(showTime) {
    if (!showTime) return "";
    const now = new Date();
    const show = new Date(showTime);
    const diffMs = show - now;
    const diffHrs = Math.round(diffMs / (1000*60*60));
    if (diffHrs < 0) return `Show Time has passed!`;
    if (diffHrs < 24) return `Less than 24 hours to Show Time!`;
    return `${Math.floor(diffHrs/24)} day(s), ${diffHrs%24} hour(s) to Show Time`;
  }

  return (
    <div className="min-h-screen flex bg-[#1a1a1a] text-white font-inter transition-all duration-300">
      {/* Left Nav */}
      <aside className={`fixed z-30 top-0 left-0 h-full bg-[#1a1a1a] shadow-lg transition-transform duration-300 ${navOpen ? 'translate-x-0' : '-translate-x-full'} sm:translate-x-0 w-64 sm:w-56 flex flex-col solana-gradient-border`} style={{borderRadius: 0}}>
        <div className="flex items-center justify-between px-6 py-5">
          <span className="text-2xl font-bold tracking-tight text-[#00D4AA]" style={{letterSpacing: '0.05em'}}>CASSaROLL</span>
          <button className="sm:hidden text-2xl text-[#00D4AA] focus:outline-none" onClick={() => setNavOpen(false)}>&times;</button>
        </div>
        <div className="mx-4 mb-4 p-3 bg-[#2a2a2a] rounded-[12px] shadow flex flex-col items-start cursor-pointer hover:bg-[#232946] transition" onClick={() => handleNavClick('cart')}>
          <div className="font-semibold text-[#00D4AA] mb-1">Cart</div>
          <div className="text-sm">{cart.length} item{cart.length !== 1 ? 's' : ''} selected</div>
        </div>
        <nav className="flex-1 flex flex-col gap-2 px-4">
          {NAV_OPTIONS.map(opt => (
            <button
              key={opt.key}
              className={`w-full text-left px-4 py-3 rounded-[12px] font-medium transition bg-transparent hover:bg-[#2a2a2a] hover:shadow focus:outline-none ${opt.key === 'shopping' && shoppingMode ? 'bg-[#00D4AA] text-white' : activeNav === opt.key ? (opt.key === 'shopping' ? 'bg-[#2a2a2a] text-[#00D4AA]' : 'bg-[#2a2a2a] text-[#00D4AA]') : ''}`}
              onClick={() => handleNavClick(opt.key)}
            >
              {opt.label}
            </button>
          ))}
        </nav>
        <div className="flex-1" />
      </aside>
      <button
        className="fixed z-40 top-4 left-4 sm:hidden bg-[#2a2a2a] text-[#00D4AA] p-2 rounded-[12px] shadow focus:outline-none"
        onClick={() => setNavOpen(true)}
        aria-label="Open menu"
      >
        <svg width="28" height="28" fill="none" viewBox="0 0 24 24"><rect y="4" width="24" height="2" rx="1" fill="#00D4AA"/><rect y="11" width="24" height="2" rx="1" fill="#00D4AA"/><rect y="18" width="24" height="2" rx="1" fill="#00D4AA"/></svg>
      </button>
      <main className="flex-1 flex flex-col sm:ml-56 ml-0 transition-all duration-300" style={mainContentStyle}>
        <div className="max-w-4xl w-full py-10 px-4 main-content">
          {/* Always show menu page unless on shopping_items */}
          {activeNav === 'menu' && (
            <section id="menu">
              <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Menu</h2>
              
              {/* Filter Sections */}
              <div className="mb-6 space-y-4">
                {/* Popular Picks Section */}
                <div>
                  <h3 className="text-sm font-semibold text-[#b0b8c1] mb-2 uppercase tracking-wide">Popular Picks</h3>
                  <div className="flex items-center gap-4">
                    <div className="flex gap-2">
                      {[
                        { key: 'top', label: 'Top Ranked' },
                        { key: 'salmon', label: 'Salmon Favorites' },
                        { key: 'tuna', label: 'Tuna Favorites' },
                        { key: 'veggie', label: 'Veggie Favorites' },
                        { key: 'all', label: 'All' },
                      ].map(f => (
                        <button
                          key={f.key}
                          className={`px-2 py-1 rounded-[8px] text-xs font-semibold border-2 transition-all duration-200
                            ${menuFilter === f.key ? 'bg-[#2a2a2a] text-white border-[#3a3a3a]' : 'bg-transparent text-[#b0b8c1] border-[#3a3a3a] hover:bg-[#2a2a2a]'}`}
                          style={{ minWidth: 80 }}
                          onClick={() => setMenuFilter(f.key)}
                        >
                          {f.label}
                        </button>
                      ))}
                    </div>
                    
                    {/* Color Legend - only show when a Popular Pick filter is active */}
                    {menuFilter !== 'all' && (
                      <div className="flex items-center gap-3 text-xs text-[#b0b8c1]">
                        <span className="font-medium">Colors:</span>
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full border border-[#FF69B4]"></div>
                          <span>Appetizer</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full border border-[#9945FF]"></div>
                          <span>Nigiri</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full border border-[#3B82F6]"></div>
                          <span>Maki</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full border border-[#00D4AA]"></div>
                          <span>Speciality</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Browse by Category Section - only show when "All" is selected */}
                {menuFilter === 'all' && (
                  <div>
                    <h3 className="text-sm font-semibold text-[#b0b8c1] mb-2 uppercase tracking-wide">Browse by Category</h3>
                    <div className="grid grid-cols-4 gap-3">
                      {orderedCategories.map((cat) => {
                        const isSelected = selectedCategories.has(cat);
                        return (
                          <button
                            key={cat}
                            className={`px-4 py-3 rounded-[12px] font-medium transition-all duration-200 text-sm ${
                              isSelected 
                                ? 'bg-[#00D4AA] text-[#1a1a1a] shadow-lg' 
                                : 'bg-[#2a2a2a] text-[#b0b8c1] hover:bg-[#3a3a3a] hover:shadow-md'
                            }`}
                            onClick={() => toggleCategoryFilter(cat)}
                          >
                            {cat}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* If a purple filter is active, show a flat grid of filtered items */}
              {menuFilter !== 'all' ? (
                (() => {
                  // Gather all menu items from all categories
                  let allItems = Object.values(menu).flat();
                  if (menuFilter === 'top') {
                    const topRanked = [
                      'oToro Nigiri',
                      'Tuna Rice Bites',
                      'Shrimp Tempura Roll',
                      'Windy City Roll',
                      'Spicy Scallop Roll',
                    ].map(n => n.toLowerCase());
                    allItems = allItems.filter(i => topRanked.includes(i.name.toLowerCase()));
                  } else if (menuFilter === 'salmon') {
                    allItems = allItems.filter(i =>
                      ([...(i.ingredients_inside||[]), ...(i.ingredients_on_top||[])]
                        .some(ing => (ing||'').toLowerCase().includes('salmon')))
                    );
                  } else if (menuFilter === 'tuna') {
                    allItems = allItems.filter(i =>
                      ([...(i.ingredients_inside||[]), ...(i.ingredients_on_top||[])]
                        .some(ing => (ing||'').toLowerCase().includes('tuna')))
                    );
                  } else if (menuFilter === 'veggie') {
                    allItems = allItems.filter(i =>
                      ([...(i.ingredients_inside||[]), ...(i.ingredients_on_top||[])]
                        .every(ing => {
                          const ingName = (ing||'').toLowerCase();
                          return ingName.includes('avocado') || ingName.includes('cucumber') || ingName.includes('asparagus') || ingName.includes('sweet potato') || ingName.includes('sprouts') || ingName.includes('jalapeno') || ingName.includes('cilantro') || ingName.includes('lime') || ingName.includes('chives');
                        }) && allItems.length > 0
                      )
                    );
                  }
                  // Sort by category order
                  const CATEGORY_ORDER = ['Appetizer', 'Nigiri', 'Maki Rolls', 'Speciality Rolls'];
                  allItems.sort((a, b) => {
                    const aIdx = CATEGORY_ORDER.indexOf(a.category);
                    const bIdx = CATEGORY_ORDER.indexOf(b.category);
                    if (aIdx !== bIdx) return aIdx - bIdx;
                    return 0;
                  });
                  // Column-major order for 2 columns
                  const numCols = 2;
                  const rows = Math.ceil(allItems.length / numCols);
                  const colMajorItems = [];
                  for (let row = 0; row < rows; row++) {
                    for (let col = 0; col < numCols; col++) {
                      const idx = col * rows + row;
                      if (allItems[idx]) colMajorItems.push(allItems[idx]);
                    }
                  }
                  return (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6">
                      {colMajorItems.map((item, idx) => {
                        const cartItem = getCartItem(item);
                        const categoryColors = {
                          'Appetizer': '#FF69B4',
                          'Nigiri': '#9945FF',
                          'Maki Rolls': '#3B82F6',
                          'Speciality Rolls': '#00D4AA'
                        };
                        const color = categoryColors[item.category] || '#666';
                        return (
                          <div
                            key={idx}
                            className="bg-[#2a2a2a] rounded-[12px] p-0 card-hover shadow-md flex flex-row items-stretch cursor-pointer transition hover:shadow-lg hover:bg-[#3a3a3a] min-h-[110px] relative border-2"
                            style={{borderRadius: 12, minHeight: 110, borderColor: color}}
                          >
                            {/* Icon section (30%) */}
                            <div className="flex items-center justify-center" style={{width: '30%', minWidth: 0}}>
                              {(() => {
                                const imgPath = getMenuItemImage(item);
                                // Try to load the image, but fallback to emoji if it fails
                                return (
                                  <img
                                    src={imgPath}
                                    alt={item.name}
                                    className="rounded-[12px] shadow-lg object-cover border-2 border-[#00D4AA]"
                                    style={{width: '80px', height: '80px', background: '#fff', objectFit: 'cover'}}
                                    onError={(e) => {
                                      // Hide the broken image completely
                                      e.target.style.display = 'none';
                                      // Check if emoji already exists to prevent duplicates
                                      const existingEmoji = e.target.parentNode.querySelector('.fallback-emoji');
                                      if (!existingEmoji) {
                                        const emojiSpan = document.createElement('span');
                                        emojiSpan.className = 'fallback-emoji block text-[3.5rem] sm:text-[4rem]';
                                        emojiSpan.style.lineHeight = '1';
                                        emojiSpan.textContent = '🍣';
                                        e.target.parentNode.appendChild(emojiSpan);
                                      }
                                    }}
                                  />
                                );
                              })()}
                            </div>
                            {/* Content section (70%) */}
                            <div className="flex flex-col justify-between flex-1 p-4">
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-lg font-semibold text-white">{item.name || 'Unnamed'}</span>
                                </div>
                                {item.description && (
                                  <div className="text-sm italic text-[#b0b8c1] mt-1 mb-2">
                                    {item.description}
                                  </div>
                                )}
                              </div>
                              <div className="flex justify-end items-end mt-auto">
                                {cartItem ? (
                                  <div className="flex items-center gap-2 bg-[#181A20] rounded-[12px] px-2 py-1 border border-[#00D4AA]">
                                    <button className="text-[#00D4AA] text-lg px-2" onClick={e => { e.stopPropagation(); setCartQuantity(item, cartItem.quantity - 1); }} disabled={cartItem.quantity <= 1}>-</button>
                                    <span className="text-white font-bold w-6 text-center">{cartItem.quantity}</span>
                                    <button className="text-[#00D4AA] text-lg px-2" onClick={e => { e.stopPropagation(); setCartQuantity(item, cartItem.quantity + 1); }} disabled={cartItem.quantity >= 5}>+</button>
                                    <button className="ml-2 text-xs text-[#b0b8c1] hover:text-red-400" onClick={e => { e.stopPropagation(); removeFromCart(item); }}>Remove</button>
                                  </div>
                                ) : (
                                  <button
                                    className="flex items-center gap-1 px-3 py-1 rounded-[12px] text-sm font-semibold border transition shadow bg-[#00D4AA] text-[#1a1a1a] border-white hover:bg-[#1a1a1a] hover:text-[#00D4AA] hover:border-[#00D4AA]"
                                    onClick={e => { e.stopPropagation(); addToCart(item); }}
                                  >
                                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M6 6h15l-1.5 9h-13z" stroke="#00D4AA" strokeWidth="2"/><circle cx="9" cy="21" r="1" fill="#00D4AA"/><circle cx="19" cy="21" r="1" fill="#00D4AA"/></svg>
                                    Add to Cart
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()
              ) : (
                <>
                  
                  {/* Collapsible Categories */}
                  <div className="space-y-6">
                    {filteredCategories.map((cat) => (
                      <div key={cat}>
                        {(() => {
                          const categoryColors = {
                            'Appetizer': '#FF69B4',
                            'Nigiri': '#9945FF', 
                            'Maki Rolls': '#3B82F6',
                            'Speciality Rolls': '#00D4AA'
                          };
                          const color = categoryColors[cat] || '#00D4AA';
                          return (
                            <button
                              className="w-full text-left text-xl font-bold mb-2 flex items-center justify-between focus:outline-none bg-[#2a2a2a] rounded-[12px] px-4 py-3 hover:shadow-md transition border-2"
                              style={{borderRadius: 12, borderColor: color, color: color}}
                              onClick={() => toggleCategory(cat)}
                            >
                              <span>{cat}</span>
                              <span className={`transition-transform ${openCategories[cat] ? 'rotate-90' : ''}`}>▶</span>
                            </button>
                          );
                        })()}
                        <div className={`overflow-hidden transition-all duration-300 ${openCategories[cat] ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}`}>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            {menu[cat].map((item, idx) => {
                              const cartItem = getCartItem(item);
                              return (
                                <div
                                  key={idx}
                                  className="bg-[#2a2a2a] rounded-[12px] p-0 card-hover shadow-md flex flex-row items-stretch cursor-pointer transition hover:shadow-lg hover:bg-[#3a3a3a] min-h-[110px]"
                                  style={{borderRadius: 12, minHeight: 110}}
                                >
                                  {/* Icon section (30%) */}
                                  <div className="flex items-center justify-center" style={{width: '30%', minWidth: 0}}>
                                    {(() => {
                                      const imgPath = getMenuItemImage(item);
                                      // Try to load the image, but fallback to emoji if it fails
                                      return (
                                        <img
                                          src={imgPath}
                                          alt={item.name}
                                          className="rounded-[12px] shadow-lg object-cover border-2 border-[#00D4AA]"
                                          style={{width: '80px', height: '80px', background: '#fff', objectFit: 'cover'}}
                                          onError={(e) => {
                                            // Hide the broken image completely
                                            e.target.style.display = 'none';
                                            // Check if emoji already exists to prevent duplicates
                                            const existingEmoji = e.target.parentNode.querySelector('.fallback-emoji');
                                            if (!existingEmoji) {
                                              const emojiSpan = document.createElement('span');
                                              emojiSpan.className = 'fallback-emoji block text-[3.5rem] sm:text-[4rem]';
                                              emojiSpan.style.lineHeight = '1';
                                              emojiSpan.textContent = '🍣';
                                              e.target.parentNode.appendChild(emojiSpan);
                                            }
                                          }}
                                        />
                                      );
                                    })()}
                                  </div>
                                  {/* Content section (70%) */}
                                  <div className="flex flex-col justify-between flex-1 p-4">
                                    <div>
                                      <div className="flex items-center gap-2">
                                        <span className="text-lg font-semibold text-white">{item.name || 'Unnamed'}</span>
                                      </div>
                                      {item.description && (
                                        <div className="text-sm italic text-[#b0b8c1] mt-1 mb-2">
                                          {item.description}
                                        </div>
                                      )}
                                    </div>
                                    <div className="flex justify-end items-end mt-auto">
                                      {cartItem ? (
                                        <div className="flex items-center gap-2 bg-[#181A20] rounded-[12px] px-2 py-1 border border-[#00D4AA]">
                                          <button className="text-[#00D4AA] text-lg px-2" onClick={e => { e.stopPropagation(); setCartQuantity(item, cartItem.quantity - 1); }} disabled={cartItem.quantity <= 1}>-</button>
                                          <span className="text-white font-bold w-6 text-center">{cartItem.quantity}</span>
                                          <button className="text-[#00D4AA] text-lg px-2" onClick={e => { e.stopPropagation(); setCartQuantity(item, cartItem.quantity + 1); }} disabled={cartItem.quantity >= 5}>+</button>
                                          <button className="ml-2 text-xs text-[#b0b8c1] hover:text-red-400" onClick={e => { e.stopPropagation(); removeFromCart(item); }}>Remove</button>
                                        </div>
                                      ) : (
                                        <button
                                          className="flex items-center gap-1 px-3 py-1 rounded-[12px] text-sm font-semibold border transition shadow bg-[#00D4AA] text-[#1a1a1a] border-white hover:bg-[#1a1a1a] hover:text-[#00D4AA] hover:border-[#00D4AA]"
                                          onClick={e => { e.stopPropagation(); addToCart(item); }}
                                        >
                                          <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M6 6h15l-1.5 9h-13z" stroke="#00D4AA" strokeWidth="2"/><circle cx="9" cy="21" r="1" fill="#00D4AA"/><circle cx="19" cy="21" r="1" fill="#00D4AA"/></svg>
                                          Add to Cart
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </section>
          )}
          {activeNav === 'runbook' && (
            <section id="runbook" className="w-full">
              <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Runbook</h2>
              
              {/* Filter Buttons */}
              <div className="mb-6 flex flex-col sm:flex-row items-start gap-4 w-full">
                <div className="flex gap-3">
                  <button
                    className={`px-4 py-2 rounded-[12px] font-medium transition-all duration-200 text-sm ${
                      runbookFilter === 'beginner' 
                        ? 'bg-[#00D4AA] text-[#1a1a1a] shadow-lg' 
                        : 'bg-[#2a2a2a] text-[#b0b8c1] hover:bg-[#3a3a3a] hover:shadow-md'
                    }`}
                    onClick={() => setRunbookFilter('beginner')}
                  >
                    Beginner Steps
                  </button>
                  <button
                    className={`px-4 py-2 rounded-[12px] font-medium transition-all duration-200 text-sm ${
                      runbookFilter === 'advanced' 
                        ? 'bg-[#00D4AA] text-[#1a1a1a] shadow-lg' 
                        : 'bg-[#2a2a2a] text-[#b0b8c1] hover:bg-[#3a3a3a] hover:shadow-md'
                    }`}
                    onClick={() => setRunbookFilter('advanced')}
                  >
                    Advanced Steps
                  </button>
                </div>
                
              </div>
              
              {loading && <div className="text-[#00D4AA]">Loading runbook...</div>}
              {error && <div className="text-red-400">{error}</div>}
              {!loading && !error && (
                <div className="w-full max-w-4xl">
                  <div className="overflow-x-auto rounded-[12px] bg-[#2a2a2a] p-4 shadow">
                    <table className="min-w-full text-sm">
                      <colgroup>
                        <col style={{width: '100px'}} />
                        <col style={{width: '400px'}} />
                      </colgroup>
                      <thead>
                        <tr>
                          <th className="px-4 py-2 text-left text-[#00D4AA] font-bold whitespace-nowrap">Timeline</th>
                          <th className="px-4 py-2 text-left text-[#00D4AA] font-bold whitespace-nowrap">Activity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          // Smart timeline sorting: T-5 days → T-1 day → T-x hours → T-x minutes → T-0
                          const getTimelineOrder = (timeline) => {
                            const timelineStr = timeline.toString().toUpperCase();
                            
                            // Days (T-5, T-4, T-3, T-2, T-1) - reverse order
                            if (timelineStr.includes('T-') && (timelineStr.includes('DAY') || timelineStr.includes('DAYS'))) {
                              const dayMatch = timelineStr.match(/T-(\d+)/);
                              if (dayMatch) {
                                const dayNum = parseInt(dayMatch[1]);
                                return 100 - dayNum; // T-5 = 95, T-4 = 96, T-3 = 97, T-2 = 98, T-1 = 99
                              }
                            }
                            
                            // Hours (T-4H, T-3H, T-2H, T-1H) - reverse order
                            if (timelineStr.includes('T-') && (timelineStr.includes('H') || timelineStr.includes('HOUR') || timelineStr.includes('HOURS'))) {
                              const hourMatch = timelineStr.match(/T-(\d+)H/);
                              if (hourMatch) {
                                const hourNum = parseInt(hourMatch[1]);
                                return 200 - hourNum; // T-4H = 196, T-3H = 197, T-2H = 198, T-1H = 199
                              }
                            }
                            
                            // Minutes (T-30M, T-15M, T-5M, etc.) - reverse order
                            if (timelineStr.includes('T-') && timelineStr.includes('M')) {
                              const minMatch = timelineStr.match(/T-(\d+)M/);
                              if (minMatch) {
                                const minNum = parseInt(minMatch[1]);
                                return 300 - minNum; // T-30M = 270, T-15M = 285, T-5M = 295
                              }
                            }
                            
                            // T-0 (final)
                            if (timelineStr === 'T-0') {
                              return 300;
                            }
                            
                            // Default fallback
                            return 999;
                          };
                          
                          // Filter items based on selected filter
                          const filteredRunbook = runbook.filter(item => {
                            if (runbookFilter === 'beginner') {
                              return item.has_beginner;
                            } else {
                              return item.has_advanced;
                            }
                          });
                          
                          const sorted = [...filteredRunbook].sort((a, b) => {
                            const aOrder = getTimelineOrder(a.timeline);
                            const bOrder = getTimelineOrder(b.timeline);
                            return aOrder - bOrder;
                          });
                          return sorted.map((item, idx) => {
                            const globalIdx = runbook.indexOf(item);
                            const isSelected = selectedRunbookItem === item;
                            const stepText = runbookFilter === 'beginner' ? item.beginner_steps : item.advanced_steps;
                            return (
                              <tr
                                key={idx}
                                className={`border-b border-[#1a1a1a] transition cursor-pointer
                                  ${isSelected ? 'border-l-8 border-[#14F195] bg-[#181A20] text-white font-bold' : 'hover:bg-[#3a3a3a]'} relative`}
                                onClick={() => {
                                  setSelectedRunbookItem(item);
                                }}
                              >
                                <td className="px-4 py-2 whitespace-nowrap font-bold" style={{ color: isSelected ? '#fff' : '#00D4AA' }}>
                                  {item.timeline}
                                </td>
                                <td className="px-4 py-2">
                                  <div className="font-bold text-white">{item.activity}</div>
                                </td>
                              </tr>
                            );
                          });
                        })()}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}
          {activeNav === 'shopping_items' && (
            <section id="shopping-items" className="w-full">
              <div className="w-full max-w-4xl">
                <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Shopping Items</h2>
                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-4 items-end">
                  <div>
                    <label className="block text-xs mb-1 text-[#b0b8c1]">Category</label>
                    <select className="bg-[#181A20] text-white rounded px-2 py-1" value={shoppingCategory} onChange={e => setShoppingCategory(e.target.value)}>
                      <option value="">All</option>
                      {uniqueCategories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs mb-1 text-[#b0b8c1]">Store</label>
                    <select className="bg-[#181A20] text-white rounded px-2 py-1" value={shoppingStore} onChange={e => setShoppingStore(e.target.value)}>
                      <option value="">All</option>
                      {uniqueStores.map(store => <option key={store} value={store}>{store}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs mb-1 text-[#b0b8c1]">Name</label>
                    <input className="bg-[#181A20] text-white rounded px-2 py-1" value={shoppingName} onChange={e => setShoppingName(e.target.value)} placeholder="Search name..." />
                  </div>
                </div>
                <div className="overflow-x-auto rounded-[12px] bg-[#2a2a2a] p-4 shadow">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr>
                        {ingredientColumns.map(col => (
                          <th
                            key={col.key}
                            className="px-4 py-2 text-left text-[#00D4AA] font-bold whitespace-nowrap cursor-pointer select-none"
                            onClick={() => setShoppingSort(s => s.key === col.key ? { key: col.key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: col.key, dir: 'asc' })}
                          >
                            {col.label}
                            {shoppingSort.key === col.key && (shoppingSort.dir === 'asc' ? ' ▲' : ' ▼')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredIngredients.map((ing, idx) => (
                        <tr key={idx} className="border-b border-[#1a1a1a] hover:bg-[#3a3a3a] transition">
                          {ingredientColumns.map(col => (
                            <td key={col.key} className="px-4 py-2 whitespace-nowrap text-white">
                              {col.key === 'cost' || col.key === 'unit_cost' ? `$${Number(ing[col.key]).toFixed(2)}` :
                               col.key === 'name' ? (ing.shopping_cart_name || ing.name || '') :
                               ing[col.key] || ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}
          {activeNav === 'recipes' && (
            <section id="recipes" className="w-full">
              <div className="w-full max-w-4xl">
                <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Recipes</h2>
                
                {/* Recipe Filters */}
                <div className="flex flex-wrap gap-4 mb-6 items-end">
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-xs mb-1 text-[#b0b8c1]">Search Recipes</label>
                    <input 
                      className="w-full bg-[#181A20] text-white rounded px-3 py-2 border border-[#3a3a3a] focus:border-[#00D4AA] focus:outline-none" 
                      value={recipeFilter} 
                      onChange={e => setRecipeFilter(e.target.value)} 
                      placeholder="Search recipes..." 
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1 text-[#b0b8c1]">Category</label>
                    <select 
                      className="bg-[#181A20] text-white rounded px-3 py-2 border border-[#3a3a3a] focus:border-[#00D4AA] focus:outline-none" 
                      value={selectedCategory} 
                      onChange={e => setSelectedCategory(e.target.value)}
                    >
                      <option value="">All Categories</option>
                      {recipeCategories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Recipe Cards */}
                <div className="grid gap-4">
                  {filteredRecipes.map(recipe => (
                    <div 
                      key={recipe.id} 
                      className="bg-[#2a2a2a] rounded-[12px] p-4 shadow hover:bg-[#3a3a3a] transition cursor-pointer"
                      onClick={() => setSelectedRecipe(recipe)}
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-lg font-semibold text-[#00D4AA] mb-1">{recipe.name}</h3>
                          <div className="flex gap-3 text-sm text-[#b0b8c1]">
                            <span className="bg-[#3a3a3a] px-2 py-1 rounded">{recipe.category}</span>
                            <span>⏱️ {recipe.prepTime}</span>
                            <span>📊 {recipe.difficulty}</span>
                          </div>
                        </div>
                        <div className="text-[#b0b8c1] text-sm">
                          Click to view details →
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {filteredRecipes.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-[#b0b8c1] text-lg">No recipes found</div>
                    <div className="text-[#b0b8c1] text-sm">Try adjusting your search or category filter</div>
                  </div>
                )}
              </div>
            </section>
          )}
          {activeNav === 'cart' && (
            <section id="cart" className="w-full">
              <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Shopping Cart</h2>
              {cart.length === 0 ? (
                <div className="text-[#b0b8c1]">Your cart is empty.</div>
              ) : (
                <div className="space-y-4">
                  <table className="min-w-full text-sm bg-[#2a2a2a] rounded-[12px] shadow">
                    <thead>
                      <tr>
                        <th className="px-4 py-2 text-left text-[#00D4AA] font-bold">Item</th>
                        <th className="px-4 py-2 text-left text-[#00D4AA] font-bold">Category</th>
                        <th className="px-4 py-2 text-left text-[#00D4AA] font-bold">Quantity</th>
                        <th className="px-4 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        // Group cart items by category, sort each group alphabetically, then flatten
                        const groupedByCategory = {};
                        cart.forEach(item => {
                          if (!groupedByCategory[item.category]) {
                            groupedByCategory[item.category] = [];
                          }
                          groupedByCategory[item.category].push(item);
                        });
                        
                        // Sort each category group alphabetically by name
                        Object.keys(groupedByCategory).forEach(category => {
                          groupedByCategory[category].sort((a, b) => a.name.localeCompare(b.name));
                        });
                        
                        // Flatten back to single array, maintaining category order
                        const sortedCart = [];
                        const categoryOrder = ['Appetizer', 'Nigiri', 'Maki Rolls', 'Speciality Rolls'];
                        categoryOrder.forEach(category => {
                          if (groupedByCategory[category]) {
                            sortedCart.push(...groupedByCategory[category]);
                          }
                        });
                        
                        return sortedCart.map((item, idx) => (
                          <tr key={idx} className="border-b border-[#1a1a1a]">
                            <td className="px-4 py-2 font-semibold text-white">{item.name}</td>
                            <td className="px-4 py-2 text-[#b0b8c1]">{item.category}</td>
                            <td className="px-4 py-2 text-white">{item.quantity}</td>
                            <td className="px-4 py-2">
                              <button className="text-xs text-[#b0b8c1] hover:text-red-400" onClick={() => removeFromCart(item)}>Remove</button>
                            </td>
                          </tr>
                        ));
                      })()}
                    </tbody>
                  </table>
                  <div className="flex justify-end items-center mt-4">
                    <button
                      className="bg-[#00D4AA] text-[#1a1a1a] px-4 py-2 rounded-[12px] font-semibold shadow hover:bg-[#1a1a1a] hover:text-[#00D4AA] border border-[#00D4AA] transition"
                      onClick={() => window.print()}
                    >
                      Print / Export
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </main>
      
      {/* Shopping List Page - Full Width */}
      {activeNav === 'shopping_list' && (
        <section id="shopping-list" className="w-full py-10 px-4">
          <div className="w-full">
            <h2 className="text-2xl font-semibold mb-6 text-[#00D4AA]">Shopping List</h2>
            
            {cart.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-[#b0b8c1] text-lg mb-4">Your cart is empty</div>
                <div className="text-[#b0b8c1] text-sm">Add items to your cart from the Menu page to see your shopping list</div>
              </div>
            ) : (
              <>
                {/* Export Controls */}
                <div className="flex justify-start gap-4 mb-6">
                  <button
                    className="bg-[#00D4AA] text-[#1a1a1a] px-4 py-2 rounded-[8px] font-semibold shadow hover:bg-[#1a1a1a] hover:text-[#00D4AA] border border-[#00D4AA] transition flex items-center gap-2"
                    onClick={() => {
                      // Group by store (only need to buy ingredients)
                      const storeGroups = {};
                      needToBuyIngredients.forEach(ing => {
                        const store = ing.store || 'Other';
                        if (!storeGroups[store]) {
                          storeGroups[store] = [];
                        }
                        storeGroups[store].push(ing);
                      });
                      
                      const lines = [];
                      Object.keys(storeGroups).sort().forEach(store => {
                        lines.push(`${store}:`);
                        storeGroups[store].forEach(ing => {
                          lines.push(`  • ${ing.name}${ing.category ? ` (${ing.category})` : ''}`);
                        });
                        lines.push('');
                      });
                      navigator.clipboard.writeText(lines.join('\n'));
                    }}
                  >
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
                      <path d="M3 7h18l-1.5 9h-15L3 7z" stroke="currentColor" strokeWidth="2"/>
                      <path d="M8 11h8" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                    Export by Store
                  </button>
                  <button
                    className="bg-[#00D4AA] text-[#1a1a1a] px-4 py-2 rounded-[8px] font-semibold shadow hover:bg-[#1a1a1a] hover:text-[#00D4AA] border border-[#00D4AA] transition flex items-center gap-2"
                    onClick={() => {
                      // Group by category (only need to buy ingredients)
                      const categoryGroups = {};
                      needToBuyIngredients.forEach(ing => {
                        const category = ing.category || 'Other';
                        if (!categoryGroups[category]) {
                          categoryGroups[category] = [];
                        }
                        categoryGroups[category].push(ing);
                      });
                      
                      const lines = [];
                      Object.keys(categoryGroups).sort().forEach(category => {
                        lines.push(`${category}:`);
                        categoryGroups[category].forEach(ing => {
                          lines.push(`  • ${ing.name}${ing.store ? ` (${ing.store})` : ''}`);
                        });
                        lines.push('');
                      });
                      navigator.clipboard.writeText(lines.join('\n'));
                    }}
                  >
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
                      <path d="M4 6h16M4 10h16M4 14h16M4 18h16" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                    Export by Category
                  </button>
                </div>

                {/* Shopping List Tables - Side by Side */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-6">
                  {/* Need to Buy Table */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-[#00D4AA]">Need to Buy</h3>
                    <div className="overflow-x-auto rounded-[12px] bg-[#2a2a2a] shadow">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-[#3a3a3a]">
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'store' ? { key: 'store', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'store', dir: 'asc' })}
                            >
                              Store {shoppingListSort.key === 'store' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'category' ? { key: 'category', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'category', dir: 'asc' })}
                            >
                              Category {shoppingListSort.key === 'category' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'name' ? { key: 'name', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'name', dir: 'asc' })}
                            >
                              Name {shoppingListSort.key === 'name' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th className="px-2 py-3 text-left text-[#00D4AA] font-bold text-xs">
                              Qty
                            </th>
                            <th className="px-4 py-3 text-left text-[#00D4AA] font-bold">
                              Action
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {needToBuyIngredients.map((ing, idx) => (
                            <tr key={idx} className="border-b border-[#1a1a1a] hover:bg-[#3a3a3a] transition">
                              <td className="px-4 py-3 text-white font-medium">{ing.store || '-'}</td>
                              <td className="px-4 py-3 text-[#b0b8c1]">{ing.category || '-'}</td>
                              <td className="px-4 py-3 text-white">{ing.shopping_cart_name || ing.name || '-'}</td>
                              <td className="px-2 py-3 text-white text-xs">{ing.totalQty || ing.quantity || '1'}</td>
                              <td className="px-4 py-3">
                                <button
                                  className="bg-[#00D4AA] text-[#1a1a1a] px-3 py-1 rounded hover:bg-[#1a1a1a] hover:text-[#00D4AA] transition"
                                  onClick={() => markAsAlreadyHave(ing)}
                                >
                                  Already have
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Already Have Table */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-[#00D4AA]">Already Have</h3>
                    <div className="overflow-x-auto rounded-[12px] bg-[#2a2a2a] shadow">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-[#3a3a3a]">
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'store' ? { key: 'store', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'store', dir: 'asc' })}
                            >
                              Store {shoppingListSort.key === 'store' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'category' ? { key: 'category', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'category', dir: 'asc' })}
                            >
                              Category {shoppingListSort.key === 'category' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th 
                              className="px-4 py-3 text-left text-[#00D4AA] font-bold cursor-pointer select-none hover:bg-[#3a3a3a] transition"
                              onClick={() => setShoppingListSort(s => s.key === 'name' ? { key: 'name', dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: 'name', dir: 'asc' })}
                            >
                              Name {shoppingListSort.key === 'name' && (shoppingListSort.dir === 'asc' ? ' ▲' : ' ▼')}
                            </th>
                            <th className="px-2 py-3 text-left text-[#00D4AA] font-bold text-xs">Qty</th>
                            <th className="px-4 py-3 text-left text-[#00D4AA] font-bold">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {alreadyHaveList.map((ing, idx) => (
                            <tr key={idx} className="border-b border-[#1a1a1a] hover:bg-[#3a3a3a] transition">
                              <td className="px-4 py-3 text-white font-medium">{ing.store || '-'}</td>
                              <td className="px-4 py-3 text-[#b0b8c1]">{ing.category || '-'}</td>
                              <td className="px-4 py-3 text-white">{ing.shopping_cart_name || ing.name || '-'}</td>
                              <td className="px-2 py-3 text-white text-xs">{ing.totalQty || ing.quantity || '1'}</td>
                              <td className="px-4 py-3">
                                <button
                                  className="bg-[#9945FF] text-white px-3 py-1 rounded hover:bg-[#7c3aed] transition"
                                  onClick={() => unmarkAsAlreadyHave(ing)}
                                >
                                  Need to buy
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div className="mt-4 text-sm text-[#b0b8c1]">
                  Showing {needToBuyIngredients.length} ingredients to buy
                  {Object.keys(groupedShoppingList).length > 0 && (
                    <span className="ml-2">
                      across {Object.keys(groupedShoppingList).length} categories
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
        </section>
      )}
      {/* Shopping Cart (right) - only on menu page */}
      <aside className={`shopping-cart fixed top-0 right-0 h-full w-[300px] bg-[#2a2a2a] shadow-2xl z-40 p-6 flex flex-col gap-4 rounded-l-[18px] border-l border-[#00D4AA] animate-float-cart transition-all duration-300 ${(activeNav === 'menu' && cart.length > 0) ? '' : 'hidden'}`} style={{boxShadow: '0 8px 32px 0 #00D4AA55'}}>
        <h2 className="text-xl font-bold mb-2 text-[#00D4AA]">Shopping Cart</h2>
        {/* Top: Menu item summary */}
        <div className="mb-4">
          {getCartSummary(cart).length === 0 && <div className="text-[#b0b8c1] italic">No items selected.</div>}
          {getCartSummary(cart).map((item, idx) => (
            <div key={idx} className="bg-[#1a1a1a] rounded-[12px] px-3 py-2 text-white text-sm flex items-center justify-between mb-2">
              <span>{item.count}x {item.name}</span>
              <span className="text-xs text-[#b0b8c1]">{item.category}</span>
            </div>
          ))}
        </div>
        {/* Categorized ingredient list */}
        {(() => {
          const cartIngredients = getCartIngredients(cart, ingredients);
          const categorized = categorizeIngredients({ all: cartIngredients });
          return (
            <div className="flex-1 overflow-y-auto">
              {Object.entries(categorized).map(([cat, items]) => (
                items.length > 0 && (
                  <div key={cat} className="mb-3">
                    <h3 className="text-lg font-semibold mb-1 text-[#00D4AA]">{cat}</h3>
                    <ul className="space-y-1">
                      {items
                        .sort((a, b) => a.name.localeCompare(b.name))
                        .map((ing, idx) => (
                          <li key={idx} className="bg-[#1a1a1a] rounded-[12px] px-3 py-2 text-white text-sm flex items-center">
                            <span>{ing.name}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                )
              ))}
            </div>
          );
        })()}
      </aside>
      
      {/* Tips Panel (right) - only on runbook page */}
      <aside className={`tips-panel fixed top-0 right-0 h-full w-[300px] bg-[#2a2a2a] shadow-2xl z-40 p-6 flex flex-col gap-4 rounded-l-[18px] border-l border-[#00D4AA] transition-all duration-300 ${(activeNav === 'runbook' && selectedRunbookItem) ? '' : 'hidden'}`} style={{boxShadow: '0 8px 32px 0 #00D4AA55'}}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-[#00D4AA]">Tips</h2>
          <button 
            className="text-[#b0b8c1] hover:text-white transition"
            onClick={() => setSelectedRunbookItem(null)}
          >
            ✕
          </button>
        </div>
        {selectedRunbookItem && (
          <div className="flex-1 overflow-y-auto">
            <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
              <h3 className="text-lg font-semibold mb-2 text-white">{selectedRunbookItem.activity}</h3>
              {selectedRunbookItem.estimated_duration && (
                <div className="text-sm text-[#00D4AA] mb-3">⏱️ {selectedRunbookItem.estimated_duration}</div>
              )}
            </div>
            
            {/* Beginner Steps */}
            {selectedRunbookItem.beginner_steps && (
              <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
                <h4 className="text-md font-semibold mb-3 text-[#00D4AA]">Beginner Steps</h4>
                <div className="text-sm text-white" style={{whiteSpace: 'normal', lineHeight: '1.5'}}>
                  {selectedRunbookItem.beginner_steps}
                </div>
              </div>
            )}
            
            {/* Advanced Steps */}
            {selectedRunbookItem.advanced_steps && (
              <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
                <h4 className="text-md font-semibold mb-3 text-[#00D4AA]">Advanced Steps</h4>
                <div className="text-sm text-white" style={{whiteSpace: 'normal', lineHeight: '1.5'}}>
                  {selectedRunbookItem.advanced_steps}
                </div>
              </div>
            )}
            
            {/* Notes */}
            {selectedRunbookItem.notes && (
              <div className="bg-[#1a1a1a] rounded-[12px] p-4">
                <h4 className="text-md font-semibold mb-2 text-[#00D4AA]">Notes</h4>
                <div className="text-sm text-white" style={{whiteSpace: 'normal', lineHeight: '1.5'}}>
                  {selectedRunbookItem.notes}
                </div>
              </div>
            )}
          </div>
        )}
      </aside>
      
      {/* Recipe Modal (right) - only on recipes page */}
      <aside className={`recipe-modal fixed top-0 right-0 h-full w-[400px] bg-[#2a2a2a] shadow-2xl z-40 p-6 flex flex-col gap-4 rounded-l-[18px] border-l border-[#00D4AA] transition-all duration-300 ${(activeNav === 'recipes' && selectedRecipe) ? '' : 'hidden'}`} style={{boxShadow: '0 8px 32px 0 #00D4AA55'}}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-[#00D4AA]">Recipe Details</h2>
          <button
            className="text-[#b0b8c1] hover:text-white text-2xl"
            onClick={() => setSelectedRecipe(null)}
          >
            ×
          </button>
        </div>
        
        {selectedRecipe && (
          <div className="flex-1 overflow-y-auto">
            <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
              <h3 className="text-lg font-semibold mb-2 text-white">{selectedRecipe.name}</h3>
              <div className="flex gap-3 text-sm text-[#b0b8c1] mb-3">
                <span className="bg-[#3a3a3a] px-2 py-1 rounded">{selectedRecipe.category}</span>
                <span>⏱️ {selectedRecipe.prepTime}</span>
                <span>📊 {selectedRecipe.difficulty}</span>
              </div>
              <p className="text-sm text-white">{selectedRecipe.description}</p>
            </div>
            
            <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
              <h4 className="text-md font-semibold mb-3 text-[#00D4AA]">Ingredients</h4>
              <ul className="space-y-2">
                {selectedRecipe.ingredients.map((ingredient, idx) => (
                  <li key={idx} className="text-sm text-white flex justify-between">
                    <span>{ingredient.name}</span>
                    <span className="text-[#b0b8c1]">{ingredient.amount}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-[#1a1a1a] rounded-[12px] p-4 mb-4">
              <h4 className="text-md font-semibold mb-3 text-[#00D4AA]">Instructions</h4>
              <div className="text-sm text-white" style={{whiteSpace: 'normal', lineHeight: '1.5'}}>
                {selectedRecipe.instructions}
              </div>
            </div>
            
            {selectedRecipe.storage && (
              <div className="bg-[#1a1a1a] rounded-[12px] p-4">
                <h4 className="text-md font-semibold mb-2 text-[#00D4AA]">Storage</h4>
                <div className="text-sm text-white">
                  {selectedRecipe.storage}
                </div>
              </div>
            )}
          </div>
        )}
      </aside>
      
      <style>{`
        .main-content {
          transition: margin-right 0.3s;
        }
        .solana-gradient-border {
          border-right: 2px solid;
          border-image: linear-gradient(180deg, #00D4AA 0%, #9945FF 100%) 1;
        }
        @keyframes float-cart {
          0% { box-shadow: 0 8px 32px 0 #00D4AA55, 0 0 0 0 #00D4AA33; }
          50% { box-shadow: 0 16px 48px 0 #00D4AA99, 0 0 16px 4px #00D4AA33; }
          100% { box-shadow: 0 8px 32px 0 #00D4AA55, 0 0 0 0 #00D4AA33; }
        }
        .animate-float-cart {
          animation: float-cart 3s ease-in-out infinite;
        }
        .card-hover {
          transition: box-shadow 0.2s, background 0.2s;
        }
        .card-hover:hover {
          box-shadow: 0 4px 24px 0 #00D4AA33;
          background: #3a3a3a;
        }
        @media print {
          aside, .main-content > :not(#cart) { display: none !important; }
          #cart { display: block !important; }
          body { background: #fff !important; color: #000 !important; }
          #cart { color: #000 !important; background: #fff !important; }
          #cart table { background: #fff !important; color: #000 !important; }
          #cart th, #cart td { color: #000 !important; }
          #cart button { display: none !important; }
          #cart .text-[#00D4AA] { color: #000 !important; }
        }
      `}</style>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />); 