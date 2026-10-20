vim.g.mapleader = ' '
vim.opt.termguicolors = true
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.cursorline = true
vim.opt.signcolumn = 'yes:1'
vim.opt.scrolloff = 8
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.splitright = true
vim.opt.splitbelow = true
vim.opt.laststatus = 3
vim.opt.clipboard = 'unnamedplus'
vim.opt.list = true
vim.opt.listchars = {tab='› ',trail='·',extends='❯',precedes='❮'}
vim.opt.fillchars = {vert='│',horiz='─',eob=' '}
vim.cmd('syntax enable')
local colors = {
 Normal={fg='#ece4f8',bg='#100f18'},NormalFloat={fg='#ece4f8',bg='#21172e'},
 FloatBorder={fg='#b095d1',bg='#21172e'},FloatTitle={fg='#edd7ff',bg='#21172e',bold=true},
 Comment={fg='#887899',italic=true},String={fg='#c3d8ba'},Number={fg='#f2d49c'},
 Function={fg='#c5b4ff',bold=true},Keyword={fg='#df9fe8'},Type={fg='#a5d6db'},
 Identifier={fg='#d8c2ec'},Statement={fg='#ca9ce4'},PreProc={fg='#bdc7ff'},
 CursorLine={bg='#20182b'},LineNr={fg='#624d79'},CursorLineNr={fg='#ddbeff',bold=true},
 Visual={bg='#4b345e'},StatusLine={fg='#e5d2ff',bg='#392647'},WinSeparator={fg='#7d609a'},
 Pmenu={bg='#2a1e38',fg='#e7d6fc'},PmenuSel={bg='#62467c',fg='#ffffff'},
 Search={bg='#806044',fg='#fff2d9'},IncSearch={bg='#b096d3',fg='#100f18'},
 HyruleGold={fg='#f2d49c',bg='#21172e'},Directory={fg='#c5b4ff',bold=true},
}
for group,value in pairs(colors) do vim.api.nvim_set_hl(0,group,value) end
vim.g.colors_name='hyrule-violet'
vim.opt.statusline=' ◇ HYRULE  ❯ %f %m %= ✦ %y  │  %l:%c  │  %p%% ◇ '
vim.keymap.set('n','<leader>w','<cmd>write<cr>',{desc='Kaydet'})
vim.keymap.set('n','<leader>q','<cmd>quit<cr>',{desc='Kapat'})
vim.keymap.set('n','<leader>e','<cmd>Lexplore<cr>',{desc='Dosya haritası'})
vim.keymap.set('n','<leader>p',function()
 vim.ui.input({prompt='Dosya yolu › ',completion='file'},function(path) if path and path~='' then vim.cmd.edit(vim.fn.fnameescape(path)) end end)
end,{desc='Dosya aç'})
local frame={'╔','═','╗','║','╝','═','╚','║'}
local function welcome()
 if vim.fn.argc()>0 or vim.api.nvim_buf_get_name(0)~='' or vim.bo.modified then return end
 local buf=vim.api.nvim_create_buf(false,true)
 local width=math.min(68,vim.o.columns-6);local height=math.min(19,vim.o.lines-6)
 if width<40 or height<12 then return end
 local win=vim.api.nvim_open_win(buf,true,{relative='editor',width=width,height=height,row=math.floor((vim.o.lines-height)/2)-1,col=math.floor((vim.o.columns-width)/2),style='minimal',border=frame,title=' ◇ Zihnin tapınağı ◇ ',title_pos='center'})
 local function close() if vim.api.nvim_win_is_valid(win) then vim.api.nvim_win_close(win,true) end end
 local tick=0
 local function draw()
   if not vim.api.nvim_win_is_valid(win) then return end
   tick=tick+1
   local lines={'','                  /\\','                 /__\\','                /\\  /\\','               /__\\/__\\','','              H Y R U L E','','          V I O L E T  ·  N E O V I M','','         '..({'◇','✧','✦','△'})[(tick-1)%4+1]..'   Krallığa hoş geldin, Fatih','','    e  Dosya haritası    p  Dosya aç    q  Kapat','    Space+w Kaydet      Space+e Harita','','       ╭── Rünler bilgiyle ışıldar ──╮'}
   vim.api.nvim_buf_set_lines(buf,0,-1,false,lines)
   if tick<32 then vim.defer_fn(draw,120) end
 end
 vim.keymap.set('n','q',close,{buffer=buf});vim.keymap.set('n','<Esc>',close,{buffer=buf})
 vim.keymap.set('n','e',function()close();vim.cmd('Explore')end,{buffer=buf})
 vim.keymap.set('n','p',function()close();vim.ui.input({prompt='Dosya › ',completion='file'},function(path)if path and path~='' then vim.cmd.edit(vim.fn.fnameescape(path))end end)end,{buffer=buf})
 draw()
end
vim.api.nvim_create_autocmd('VimEnter',{callback=function()vim.defer_fn(welcome,80)end})
vim.api.nvim_create_user_command('Hyrule',welcome,{})
