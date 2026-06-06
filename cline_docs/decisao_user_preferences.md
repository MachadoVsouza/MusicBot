# Preferências do Usuário

## Regras de Execução
- **NÃO** executar comandos de terminal do tipo `docker` e `curl`.
- **NÃO** executar comandos que exigem permissão ou aprovação (`requires_approval: true`).
- Apenas comandos básicos Linux seguros podem ser executados (ex: `echo`, `ls`, `cat`, `grep`).
- Comandos que envolvem redes, containers, instalação de pacotes devem ser **solicitados ao usuário** para que ele execute manualmente.
- Sempre pedir para o usuário executar comandos como `docker`, `curl`, `npm install`, etc.