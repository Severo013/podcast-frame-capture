# Podcast Frame Capture - Capturador de Emoções

Este programa captura automaticamente frames de emoções em podcasts do YouTube, utilizando inteligência artificial para detectar e categorizar expressões faciais dos participantes.

## Características

- **Detecção de Emoções**: Utiliza modelos de IA do HuggingFace para classificar emoções
- **Controle de Qualidade**: Rejeita frames borrados ou com olhos fechados
- **Anti-Duplicação**: Evita capturar múltiplos frames da mesma emoção em sequência
- **Otimizado**: Processa apenas frames estratégicos para eficiência
- **Categorização**: Organiza frames por tipo de emoção

## Instalação

1. Certifique-se de ter Python 3.8+ instalado
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Uso Básico
```bash
python FrameProcessor.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Opções Avançadas
```bash
python FrameProcessor.py "URL_DO_YOUTUBE" --output pasta_saida --skip-minutes 15 --emotion-threshold 0.8
```

### Parâmetros

- `url`: URL do YouTube do podcast (obrigatório)
- `--output, -o`: Diretório onde salvar os frames (padrão: `output_frames`)
- `--skip-minutes, -s`: Minutos a pular no início do vídeo (padrão: 10)
- `--emotion-threshold, -e`: Limiar mínimo para considerar uma emoção forte (padrão: 0.7)

## Estrutura de Saída

Os frames são organizados em pastas por emoção:
```
output_frames/
├── joy/
├── anger/
├── surprise/
├── sadness/
├── fear/
└── neutral/
```

Cada arquivo é nomeado com o formato:
`emoção_timestamp_confiança.jpg`

Exemplo: `joy_1234.5s_conf0.85.jpg`

## Funcionamento

1. **Download**: Baixa o vídeo do YouTube em qualidade otimizada
2. **Pré-processamento**: Pula os primeiros minutos (publicidades)
3. **Detecção de Faces**: Identifica rostos nos frames
4. **Controle de Qualidade**: Verifica se a imagem não está borrada e se os olhos estão abertos
5. **Classificação**: Analisa a emoção usando IA
6. **Filtragem**: Salva apenas emoções fortes e não repetitivas
7. **Organização**: Categoriza por tipo de emoção

## Configurações Avançadas

Você pode ajustar os seguintes parâmetros no código:

- `emotion_threshold`: Confiança mínima para considerar uma emoção (padrão: 0.7)
- `blur_threshold`: Limiar para detectar imagens borradas (padrão: 100.0)
- `min_time_between_same_emotion`: Tempo mínimo entre capturas da mesma emoção (padrão: 30s)
- `frame_skip`: Quantos frames pular entre análises (padrão: FPS/2)

## Requisitos de Sistema

- **CPU**: Processador moderno (recomendado: 8+ cores)
- **RAM**: Mínimo 8GB (recomendado: 16GB+)
- **GPU**: Opcional, mas acelera significativamente o processamento
- **Espaço em Disco**: Depende do tamanho do vídeo e quantidade de frames capturados

## Dicas de Performance

1. **GPU**: Se disponível, será usada automaticamente
2. **Qualidade do Vídeo**: O programa baixa em 720p para balancear qualidade e performance
3. **Frame Rate**: Processa 2 frames por segundo por padrão
4. **Memória**: Videos muito longos podem consumir bastante RAM

## Solução de Problemas

### Erro de Download
- Verifique se a URL do YouTube está correta
- Certifique-se de que o vídeo não é privado ou restrito

### Performance Lenta
- Verifique se há GPU disponível
- Reduza o `emotion_threshold` para capturar menos frames
- Aumente o `frame_skip` para processar menos frames

### Muitos/Poucos Frames
- Ajuste `emotion_threshold` (0.5-0.9)
- Modifique `min_time_between_same_emotion`

## Contribuição

Para melhorar o programa:
1. Teste com diferentes tipos de podcasts
2. Ajuste os parâmetros conforme necessário
3. Reporte bugs ou sugestões

## Licença

Este projeto é de uso livre para fins educacionais e pessoais.
