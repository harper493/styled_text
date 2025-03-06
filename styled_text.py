from __future__ import annotations
from enum import Enum
from typing import Iterable
import sys
import os

class StyledText:

    render_style_plain = 0
    render_style_iso6429 = 1

    render_style = 1 if sys.stdout.isatty() else 0

    color_map = {
        'none' : 0,
        'black' : 232,
        'red' : 9,
        'green' : 40,
        'dark_green' : 34,
        'yellow' : 11,
        'blue' : 20,
        'magenta' : 90,
        'cyan' : 14,
        'white' : 15,
        'grey' : 244,
        'deep_blue' : 20,
        'mid_blue' : 27,
        'orange' : 208,
        'pink' : 201,
        'brown' : 1,
    }

    style_map = {
        'none' : 0,
        'bold' : 1,
        'italic' : 3,
        'blink' : 5,
        'underline' : 4,
        'crossed' : 9,
        'inverted' : 7,
    }

    def __init__(self,
                 text: str|StyledText|Iterable[StyledText] = '',
                 color: str|None = None,
                 background: str|None = None,
                 style: str|Iterable[str]|None = None,
                 size: float=0 ):
        self.color = color
        self.background = background
        self.style = style
        self.size = size
        self.subtexts: list[StyledText] = []
        if isinstance(text, str):
            self.text = text
        elif isinstance(text, StyledText):
            self.text = ''
            self.subtexts = [ text ]
        else:
            self.text = ''
            self.subtexts = [ s for s in text ]

    def copy(self) -> StyledText:
        st = StyledText(self.text,
                        color=self.color,
                        background=self.background,
                        style = self.style,
                        size = self.size)
        st.subtexts = self.subtexts.copy()
        return st

    def _make_subtext(self) -> StyledText:
        if not self.subtexts and self.text:
            self.subtexts = [ self.copy() ]
        self.text = ''
        return self

    def __iadd__(self, other: str|StyledText) -> StyledText:
        self._make_subtext()
        if isinstance(other, str):
            self.subtexts.append(StyledText(other))
        else:
            self.subtexts.append(other)
        return self

    def __add__(self, other: str|StyledText) -> StyledText:
        result = self.copy()
        result += other
        return result

    def attach(self,
               text: str|StyledText,
               color: str|None = None,
               background: str|None = None,
               style: str|Iterable[str]|None = None,
               size: float=0 ) -> StyledText:
        self._make_subtext()
        if isinstance(text, str):
            self.subtexts.append(StyledText(text, color=color, background=background, style=style, size=size))
        else:
            self.subtexts.append(text.copy())
        self.subtexts[-1].underride_from(self)
        return self

    def override(self,
                 color: str|None = None,
                 background: str|None = None,
                 style: str|Iterable[str]|None = None,
                 size: float=0 ) -> StyledText:
        self.color = color or self.color
        self.background = background or self.background
        self.style = style or self.style
        self.size = size or self.size
        return self

    def underride(self,
                 color: str|None = None,
                  background: str|None = None,
                 style: str|Iterable[str]|None = None,
                 size: float=0 ) -> StyledText:
        self.color = self.color or color
        self.background = self.background or background
        self.style = self.style or style
        self.size = self.size or size
        return self

    def override_from(self, other: StyledText) -> StyledText:
        self.override(color=other.color, background=other.background, style=other.style, size=other.size)
        return self

    def underride_from(self, other: StyledText) -> StyledText:
        self.underride(color=other.color, background=other.background, style=other.style, size=other.size)
        return self

    def __str__(self) -> str:
        return self.render()

    def get_text(self) -> str:
        if self.subtexts:
            return ''.join([ s.get_text() for s in self.subtexts ])
        else:
            return self.text

    def render(self) -> str:
        match StyledText.render_style:
            case 0:
                return self.get_text()
            case 1:
                return self.render_iso6429()
            case _:
                return self.get_text()

    def render_iso6429(self) -> str:
        esc = '\u001b'
        csi = esc + '['
        result = ''
        if self.subtexts:
            result = ''.join([ s.render_iso6429() for s in self.subtexts ])
        else:
            if self.style:
                for ss in [self.style] if isinstance(self.style, str) else self.style:
                    result += f'{csi}{self.get_style(ss)}m'
            else:
                result += f'{csi}0m'
            if self.color:
                result += f'{csi}38;5;{self.get_color(self.color)}m'
            else:
                result += f'{csi}39m'
            if self.background:
                result += f'{csi}48;5;{self.get_color(self.background)}m'
            else:
                result += f'{csi}49m'
            result += self.text
        result += f'{csi}39m{csi}49m{csi}0m'
        #print(' '.join([ str(ord(b)) for b in result]))
        #print(' '.join([ f"'{b}'" if b!=esc else 'ESC' for b in result]))
        return result

    def get_color(self, c: str) -> int:
        return self._get_from_map(StyledText.color_map, c, 'none')

    def get_style(self, s:str) -> int:
        return self._get_from_map(StyledText.style_map, s, 'none')

    def _get_from_map(self, map: dict[str, int], s: str, dflt: str) -> int:
        try:
            return map[s]
        except KeyError:
            try:
                return int(s)
            except ValueError:
                return map[dflt]

    @staticmethod
    def set_render_style_plain() -> None:
        StyledText.render_style = 0

    @staticmethod
    def set_render_style_iso6429() -> None:
        StyledText.render_style = 1

if __name__=='__main__':
    print(StyledText('normal'))
    print(StyledText('red', color='red'))
    print(StyledText('green underline', color='green', style='underline'))
    print(StyledText('blue italic underline', color='blue', style=('italic', 'underline')))
    s1 = StyledText('magenta underline', color='magenta', style='underline')
    s1.attach(' orange underline', color='orange')
    print(s1.get_text(), s1)
    s3 = s1.attach(' orange italic', color='orange', style='italic')
    print(s3)
    s4 = StyledText((StyledText('pink', color='pink'), StyledText('bold', style='bold')))
    print(s4)
    s5 = StyledText((StyledText('pink', color='pink'),
                     StyledText((StyledText('bold', style='bold'),
                                StyledText('brown inverted', color='brown', style='inverted')))))
    print(s5)
    print('as text: ', s5.get_text())
    s6 = StyledText('cyan', color='pink')
    s6.override(color='cyan')
    print(s6)
    s7 = StyledText('magenta italic', color='magenta', style='italic')
    s7.underride(color='orange', style='bold')
    print(s7)
    print(StyledText('orange on grey', color='orange', background='grey'))
    s8 = StyledText('green', color='green').attach('blue', color='blue').attach('green')
    print(s8)
    s9 = StyledText('pink bold', color='pink', style='bold') + StyledText('normal')
    print(s9)
    print(StyledText('normal'))
    
        
                
