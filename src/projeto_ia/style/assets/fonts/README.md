# Font Awesome local

- Versão: Font Awesome Free 7.3.1.
- Fonte oficial: `font-awesome-7-free-solid-900.otf`.
- Origem: <https://github.com/FortAwesome/Font-Awesome/releases/tag/7.3.1>.
- Licença preservada em `LICENSE-FONT-AWESOME.txt`.

O arquivo OTF é a fonte de verdade para os ícones da interface. O gerador
`python -m tools.gerar_recursos_interface` rasteriza somente os glifos usados
em PNGs transparentes. Assim, o aplicativo não instala fontes no Windows e
não depende do Pillow durante o jogo.
