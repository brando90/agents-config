-- simple commands

hs.hotkey.bind({"cmd", "alt", "ctrl"}, "W", function()
    hs.alert.show("Hello World!")
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "R", function()
    hs.reload()
    number_thirds_done = 0
  end)
  hs.alert.show("Config loaded")
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "Space", function()
    local win = hs.window.focusedWindow()
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    f.x = max.x
    f.y = max.y
    f.w = max.w
    f.h = max.h
    win:setFrame(f)
    number_thirds_done = 0
  end)
  
  -- 1/2 moves of windows
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "Left", function()
    local win = hs.window.focusedWindow()
    hs.console.printStyledtext(win)
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    f.x = max.x
    --f.y = max.y
    f.w = max.w / 2
    --f.h = max.h
    win:setFrame(f)
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "Right", function()
    local win = hs.window.focusedWindow()
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    f.x = max.x + (max.w / 2)
    --f.y = max.y
    f.w = max.w / 2
    --f.h = max.h 
    win:setFrame(f)
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "Up", function()
    local win = hs.window.focusedWindow()
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    f.y = max.y
    f.h = max.h / 2
    win:setFrame(f)
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt", "ctrl"}, "Down", function()
    local win = hs.window.focusedWindow()
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    f.h = max.h / 2
    f.y = max.y + (max.h / 2)
    win:setFrame(f)
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt"}, "Left", function()
    local win = hs.window.focusedWindow()
    win:moveOneScreenWest()
    number_thirds_done = 0
  end)
  
  hs.hotkey.bind({"cmd", "alt"}, "Right", function()
    local win = hs.window.focusedWindow()
    win:moveOneScreenEast()
    number_thirds_done = 0
  end)

  -- 1/3 moves of windows
  
  -- meant to track number of times we've done thirds. It's meant so that
  -- the first one gives 2/3 to the direction given and then another time gives 1/3
  -- doing it one more time resets everything and it starts splitting from the begininng (so it does not recursively split the previous size but instead from the max size)
  -- all other commands resets this flag to 0 so that splitting to thirds can be done
  number_thirds_done = 0

  hs.hotkey.bind({"alt", "ctrl"}, "Left", function()
    local win = hs.window.focusedWindow()
    hs.console.printStyledtext(win)
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    if number_thirds_done == 0 then 
      f.x = max.x
      --f.y = max.y
      f.w = (2 / 3) * max.w 
      --f.h = max.h
      win:setFrame(f)
      number_thirds_done = 1
    elseif number_thirds_done == 1 then
      f.x = max.x
      --f.y = max.y
      f.w = (1 / 3) * max.w 
      --f.h = max.h
      win:setFrame(f)
      number_thirds_done = 2
    else
      print('done')
      number_thirds_done = 0
    end
  end)

  hs.hotkey.bind({"alt", "ctrl"}, "Right", function()
    local win = hs.window.focusedWindow()
    local f = win:frame()
    local screen = win:screen()
    local max = screen:frame()
  
    if number_thirds_done == 0 then
      f.x = max.x + (max.w / 3)
      --f.y = max.y
      f.w = (2/3) * max.w 
      --f.h = max.h
      win:setFrame(f)
      number_thirds_done = 1
    elseif number_thirds_done == 1 then
      f.x = max.x + ( (2/3) * max.w )
      --f.y = max.y
      f.w = (1/3) * max.w
      --f.h = max.h
      win:setFrame(f)
      number_thirds_done = 2
    else
      print('done')
      number_thirds_done = 0
    end
  end)
