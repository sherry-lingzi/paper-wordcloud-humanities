"""
科学文献词云生成器 - 文献配置文件
包含所有10篇目标文献的arXiv ID和基本信息
"""

PAPERS_CONFIG = [
    {
        "id": 1,
        "arxiv_id": "2211.02002",
        "title": "Emergence of Competing Orders and Possible Quantum Spin Liquid in SU(N) Fermions",
        "authors": ["Xue-Jia Yu", "Shao-Hang Shi", "Limei Xu", "Zi-Xiang Li"],
        "journal": "Phys. Rev. Lett. 132, 036704 (2024)",
        "note": "Selected as Editor's Suggestion",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2211.02002"
    },
    {
        "id": 2,
        "arxiv_id": "2302.10115", 
        "title": "Non-Hermitian Strongly Interacting Dirac Fermions",
        "authors": ["Xue-Jia Yu", "Zhiming Pan", "Limei Xu", "Zi-Xiang Li"],
        "journal": "Phys. Rev. Lett. 132, 116503 (2024)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2302.10115"
    },
    {
        "id": 3,
        "arxiv_id": "2409.18050",
        "title": "Superconductivity and Charge Density Wave in the Holstein Model on the Penrose Lattice", 
        "authors": ["Lu Liu", "Zi-Xiang Li", "Fan Yang"],
        "journal": "Phys. Rev. Lett. 134, 206001 (2025)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2409.18050"
    },
    {
        "id": 4,
        "arxiv_id": "2308.05313",
        "title": "Bogoliubov quasiparticle on the gossamer Fermi surface in electron-doped cuprates",
        "authors": ["Ke-Jun Xu", "Qinda Guo", "Makoto Hashimoto", "Zi-Xiang Li", "Su-Di Chen", "Junfeng He", "Yu He", "Cong Li", "Magnus H Berntsen", "Costel R Rotundu", "Young S Lee", "Thomas P Devereaux", "Andreas Rydh", "Dong-Hui Lu", "Dung-Hai Lee", "Oscar Tjernberg", "Zhi-Xun Shen"],
        "journal": "Nature Physics 19, 1834 (2023)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2308.05313"
    },
    {
        "id": 5,
        "arxiv_id": "2403.19258",
        "title": "Finite-time scaling beyond the Kibble-Zurek prerequisite in Dirac systems",
        "authors": ["Zhi Zeng", "Yin-Kai Yu", "Zhi-Xuan Li", "Zi-Xiang Li", "Shuai Yin"],
        "journal": "Nat. Commun. 16, 6181 (2025)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2403.19258"
    },
    {
        "id": 6,
        "arxiv_id": "2408.04002",
        "title": "Quantum spin liquid from electron-phonon coupling",
        "authors": ["Xun Cai", "Zhaoyu Han", "Zi-Xiang Li", "Steven A. Kivelson", "Hong Yao"],
        "journal": "Proc. Natl. Acad. Sci. 122 (33) e2426111122 (2025)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2408.04002"
    },
    {
        "id": 7,
        "arxiv_id": "2409.18515",
        "title": "Correlation between unconventional superconductivity and strange metallicity revealed by operando superfluid density measurements",
        "authors": ["Ruozhou Zhang", "Mingyang Qin", "Chenyuan Li", "Zhanyi Zhao", "Zhongxu Wei", "Juan Xu", "Xingyu Jiang", "Wenxin Cheng", "Qiuyan Shi", "Xuewei Wang", "Jie Yuan", "Yangmu Li", "Qihong Chen", "Tao Xiang", "Subir Sachdev", "Zi-Xiang Li", "Kui Jin", "Zhongxian Zhao"],
        "journal": "Sci. Adv. 11, eadu0795 (2025)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2409.18515"
    },
    {
        "id": 8,
        "arxiv_id": "2410.18854",
        "title": "Preempting Fermion Sign Problem: Unveiling Quantum Criticality through Nonequilibrium Dynamics",
        "authors": ["Yin-Kai Yu", "Zhi-Xuan Li", "Shuai Yin", "Zi-Xiang Li"],
        "journal": "arXiv:2410.18854 (2024)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2410.18854"
    },
    {
        "id": 9,
        "arxiv_id": "2303.13403",
        "title": "Boosting quantum Monte Carlo and alleviating sign problem by Gutzwiller projection",
        "authors": ["Wei-Xuan Chang", "Zi-Xiang Li"],
        "journal": "Physical Review B 110, 085152 (2024)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2303.13403"
    },
    {
        "id": 10,
        "arxiv_id": "2409.06547",
        "title": "Imaginary-time Mpemba effect in quantum many-body systems",
        "authors": ["Wei-Xuan Chang", "Shuai Yin", "Shi-Xin Zhang", "Zi-Xiang Li"],
        "journal": "arXiv:2409.06547 (2024)",
        "note": "",
        "ar5iv_url": "https://ar5iv.labs.arxiv.org/html/2409.06547"
    }
]

# 科学术语词汇表 - 用于词云生成时的特殊处理
SCIENTIFIC_TERMS = [
    # 物理概念
    "quantum", "spin", "liquid", "fermions", "superconductivity", "electron", "phonon",
    "monte carlo", "dirac", "non-hermitian", "cuprates", "Holstein", "Penrose", "lattice",
    "bogoliubov", "quasiparticle", "fermi", "surface", "kibble-zurek", "mpemba", "gutzwiller",
    
    # 研究方法
    "simulation", "algorithm", "numerical", "theoretical", "experimental", "computational",
    "projector", "variational", "determinant", "sign problem", "phase diagram", "critical",
    
    # 材料和系统
    "cuprate", "superconductor", "antiferromagnetic", "insulator", "conductor", "crystal",
    "quasicrystal", "many-body", "strongly correlated", "phase transition",
    
    # 数学物理术语
    "hamiltonian", "eigenvalue", "wave function", "density", "correlation", "fluctuation",
    "universality", "scaling", "renormalization", "symmetry", "topology"
]

# 停用词 - 在生成词云时要过滤的常用学术词汇
ACADEMIC_STOPWORDS = [
    "paper", "study", "research", "result", "conclusion", "introduction", "discussion",
    "method", "approach", "technique", "analysis", "calculation", "measurement",
    "experiment", "observation", "theory", "model", "framework", "system", "case",
    "example", "instance", "section", "chapter", "figure", "table", "equation",
    "reference", "citation", "bibliography", "abstract", "summary", "review"
]