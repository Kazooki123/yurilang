PORTNAME=       yurilang
DISTVERSION=    1.6.0
CATEGORIES=     lang

MAINTAINER=     mgamerdinge146@gmail.com
COMMENT=        YuriLang esoteric programming language

LICENSE=        GPL-3

USES=           python
USE_PYTHON=     noflavors

RUN_DEPENDS=    ${PYTHON_PKGNAMEPREFIX}reportlab>0:print/py-reportlab

USE_GITHUB=     yes
GH_ACCOUNT=     Kazooki123
GH_PROJECT=     yurilang

NO_BUILD=       yes

do-install:
	@${MKDIR} ${STAGEDIR}${PREFIX}/share/yurilang
	@cd ${WRKSRC} && ${COPYTREE_SHARE} . ${STAGEDIR}${PREFIX}/share/yurilang

	@${MKDIR} ${STAGEDIR}${PREFIX}/bin
	@${ECHO_CMD} '#!/usr/bin/env python3' > ${STAGEDIR}${PREFIX}/bin/yuri
	@${ECHO_CMD} 'exec python3 ${PREFIX}/share/yurilang/main.py "$$@"' >> ${STAGEDIR}${PREFIX}/bin/yuri
	@${CHMOD} +x ${STAGEDIR}${PREFIX}/bin/yuri

.include <bsd.port.mk>

