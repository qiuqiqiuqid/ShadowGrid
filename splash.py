# -*- coding: utf-8 -*-
import random

# 多个随机启动画面（MSF风格）
splash_list = [
    r"""
  .       .       .       .       .       .
 / \     / \     / \     / \     / \     / \
( S )---( H )---( A )---( D )---( O )---( W )
 \_/     \_/     \_/     \_/     \_/     \_/
  |       |       |       |       |       |
  v       v       v       v       v       v

      ShadowGrid v1.0.1
      Secure Remote Tool
      
  scan. exploit. control.
    """,
    
    r"""
  __    __    __    __    __    __
 /  \  /  \  /  \  /  \  /  \  /  \
( S  )( S  )( S  )( S  )( S  )( S  )
 \  /  \  /  \  /  \  /  \  /  \  /
  \/    \/    \/    \/    \/    \/

      ShadowGrid v1.0.1
      Secure Remote Tool
      
  scan. exploit. control.
    """,
    
    r"""
  ___   ___   ___   ___   ___   ___
 (S _) (G _) (R _) (I _) (D _) (R _)
  | |   | |   | |   | |   | |   | |
  | |   | |   | |   | |   | |   | |
  |_|   |_|   |_|   |_|   |_|   |_|

      ShadowGrid v1.0.1
      Secure Remote Tool
      
  scan. exploit. control.
    """,
    
    r"""
  ___   ___   ___   ___   ___   ___
 (S_)  (G_)  (R_)  (I_)  (D_)  (R_)
  | |   | |   | |   | |   | |   | |
  | |   | |   | |   | |   | |   | |
  |_|   |_|   |_|   |_|   |_|   |_|

      ShadowGrid v1.0.1
      Secure Remote Tool
      
  scan. exploit. control.
    """,
    
    r"""
  _ _   _ _   _ _   _ _   _ _   _ _
 (_S)  (_G)  (_R)  (_I)  (_D)  (_R)
  | |   | |   | |   | |   | |   | |
  | |   | |   | |   | |   | |   | |
  |_|   |_|   |_|   |_|   |_|   |_|

      ShadowGrid v1.0.1
      Secure Remote Tool
      
  scan. exploit. control.
    """,
]

def get_splash():
    """随机返回一个启动画面"""
    return random.choice(splash_list)

if __name__ == "__main__":
    print(get_splash())
