from zlibraryCrowler.config import *

# Book similarity calculation using RapidFuzz + TF-IDF semantic similarity
import re
import sys
import unicodedata
from typing import Dict, List, Union, Optional
import numpy as np
import json

from rapidfuzz import fuzz, distance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize(title: str) -> str:
    """Normalize text: lowercase, remove accents/punctuation, preserve Chinese chars."""
    def is_chinese_char(char):
        return '\u4e00' <= char <= '\u9fff'
    
    # Handle simplified vs traditional Chinese conversions for better matching
    simplified_to_traditional = {
        '传': '傳', '国': '國', '学': '學', '语': '語', '汇': '匯', 
        '浒': '滸', '历': '歷', '经': '經', '应': '應', '业': '業',
        '单': '單', '双': '雙', '台': '臺', '体': '體', '丰': '豐',
        '书': '書', '东': '東', '认': '認', '办': '辦', '义': '義',
        '齐': '齊', '号': '號', '万': '萬', '与': '與', '队': '隊'
    }
    
    result = []
    for char in title:
        if is_chinese_char(char):
            # Try to normalize simplified to traditional for better matching
            normalized_char = simplified_to_traditional.get(char, char)
            result.append(normalized_char)
        else:
            normalized = unicodedata.normalize("NFKD", char) \
                                   .encode("ascii", "ignore") \
                                   .decode("ascii")
            result.append(normalized)
    
    title = ''.join(result)
    title = title.lower()
    
    # Enhanced Chinese punctuation normalization
    if any(is_chinese_char(char) for char in title):
        # Normalize Chinese punctuation
        title = re.sub(r"[·•]", "", title)  # Remove middle dots
        title = re.sub(r"[：:]", ":", title)  # Normalize colons
        title = re.sub(r"[，,]", ",", title)  # Normalize commas
        title = re.sub(r"[（(]", "(", title)  # Normalize parentheses
        title = re.sub(r"[）)]", ")", title)
        title = re.sub(r"[^\u4e00-\u9fff\w\s:,()]", " ", title)
    else:
        title = re.sub(r"[^a-z0-9\s]", " ", title)
    
    return re.sub(r"\s+", " ", title).strip()


def semantic_similarity(a: str, b: str) -> float:
    """Calculate semantic similarity using TF-IDF and cosine similarity."""
    a_norm, b_norm = normalize(a), normalize(b)
    
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    
    def has_chinese(text):
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    has_chinese_a = has_chinese(a)
    has_chinese_b = has_chinese(b)
    
    # Handle mixed language pairs (potential translations)
    if has_chinese_a != has_chinese_b:
        # Check for known translation pairs
        translation_score = check_translation_pairs(a, b)
        if translation_score > 0:
            return translation_score
        
        # For mixed language pairs without known translations, use character overlap
        chars_a, chars_b = set(a_norm), set(b_norm)
        if chars_a and chars_b:
            intersection = chars_a.intersection(chars_b)
            union = chars_a.union(chars_b)
            return len(intersection) / len(union) if union else 0.0
        return 0.0
    
    try:
        if has_chinese_a or has_chinese_b:
            # Enhanced Chinese text processing
            vectorizer = TfidfVectorizer(
                analyzer='char', ngram_range=(1, 3), lowercase=True, max_features=2000)
        else:
            vectorizer = TfidfVectorizer(
                analyzer='char_wb', ngram_range=(2, 4), lowercase=True, max_features=1000)
        
        tfidf_matrix = vectorizer.fit_transform([a_norm, b_norm])
        
        if tfidf_matrix.shape[1] == 0:
            # Fallback to character/word overlap
            if has_chinese_a or has_chinese_b:
                chars_a, chars_b = set(a_norm), set(b_norm)
                if not chars_a or not chars_b:
                    return 0.0
                intersection = chars_a.intersection(chars_b)
                union = chars_a.union(chars_b)
                return len(intersection) / len(union) if union else 0.0
            else:
                words_a, words_b = set(a_norm.split()), set(b_norm.split())
                if not words_a or not words_b:
                    return 0.0
                intersection = words_a.intersection(words_b)
                union = words_a.union(words_b)
                return len(intersection) / len(union) if union else 0.0
        
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity_matrix[0][0])
        
    except Exception:
        # Enhanced fallback for Chinese text
        if has_chinese_a or has_chinese_b:
            chars_a, chars_b = set(a_norm), set(b_norm)
            if not chars_a or not chars_b:
                return 0.0
            intersection = chars_a.intersection(chars_b)
            union = chars_a.union(chars_b)
            return len(intersection) / len(union) if union else 0.0
        else:
            words_a, words_b = set(a_norm.split()), set(b_norm.split())
            if not words_a or not words_b:
                return 0.0
            intersection = words_a.intersection(words_b)
            union = words_a.union(words_b)
            return len(intersection) / len(union) if union else 0.0


def check_translation_pairs(a: str, b: str) -> float:
    """Check if two titles are likely translations of each other."""
    # Known translation pairs (English -> Chinese)
    translation_pairs = {
        "the three-body problem": "三体",
        "three-body problem": "三体", 
        "journey to the west": "西游记",
        "dream of the red chamber": "红楼梦",
        "water margin": "水浒传",
        "outlaws of the marsh": "水浒传",
        "romance of the three kingdoms": "三国演义",
        "harry potter and the philosopher's stone": "哈利·波特与魔法石",
        "harry potter and the sorcerer's stone": "哈利·波特与魔法石",
        "one hundred years of solitude": "百年孤独",
        "fortress besieged": "围城",
        "to live": "活着",
    }
    
    a_norm = normalize(a).lower().strip()
    b_norm = normalize(b).lower().strip()
    
    # Check direct translations
    for eng, chi in translation_pairs.items():
        if (a_norm == eng and normalize(chi) == b_norm) or (b_norm == eng and normalize(chi) == a_norm):
            return 0.8  # High similarity for known translations
    
    # Check partial translations (for subtitled versions)
    for eng, chi in translation_pairs.items():
        if ((eng in a_norm or a_norm in eng) and normalize(chi) in b_norm) or \
           ((eng in b_norm or b_norm in eng) and normalize(chi) in a_norm):
            return 0.6  # Moderate similarity for partial matches
    
    return 0.0


def similarities(a: str, b: str) -> Dict[str, float]:
    """Return similarity metrics (0-1 range)."""
    a_norm, b_norm = normalize(a), normalize(b)

    return {
        "levenshtein_ratio": distance.Levenshtein.normalized_similarity(a_norm, b_norm),
        "token_sort_ratio": fuzz.token_sort_ratio(a_norm, b_norm) / 100.0,
        "token_set_ratio":  fuzz.token_set_ratio(a_norm, b_norm)  / 100.0,
        "jaro_winkler":     distance.JaroWinkler.similarity(a_norm, b_norm),
        "semantic_similarity": semantic_similarity(a, b),
    }


def comprehensive_similarity_score(a: str, b: str) -> float:
    """Calculate comprehensive similarity score with enhanced accuracy and stricter thresholds."""
    scores = similarities(a, b)
    
    # Check for perfect match first
    if a == b:
        return 1.0
    
    # Check for perfect normalized match  
    a_norm, b_norm = normalize(a), normalize(b)
    if a_norm == b_norm:
        return 1.0
    
    # Adjusted weights for better balance
    weights = {
        'levenshtein_ratio': 0.16,
        'token_sort_ratio': 0.24,
        'token_set_ratio': 0.24,  
        'jaro_winkler': 0.18,
        'semantic_similarity': 0.18,
    }
    
    weighted_score = sum(scores[metric] * weight for metric, weight in weights.items())
    
    # Enhanced regional penalty detection
    regional_penalty = detect_regional_variation(a, b)
    if regional_penalty > 0:
        weighted_score = max(0.0, weighted_score - regional_penalty)
    
    # Perfect individual scores boost (for cases like punctuation-only differences)
    perfect_scores = sum(1 for score in scores.values() if score >= 0.99)
    if perfect_scores >= 4:  # At least 4 out of 5 metrics are perfect
        weighted_score = min(1.0, weighted_score * 1.15)
    elif perfect_scores >= 3:
        weighted_score = min(1.0, weighted_score * 1.08)
    
    # More conservative high score boost
    max_individual_score = max(scores.values())
    if max_individual_score > 0.95:
        weighted_score = min(1.0, weighted_score * 1.03)
    elif max_individual_score > 0.9:
        weighted_score = min(1.0, weighted_score * 1.015)
    
    # Penalize very short matches that might be false positives
    if len(a_norm) <= 3 or len(b_norm) <= 3:
        if weighted_score > 0.8:
            weighted_score *= 0.85
    
    return weighted_score


def extract_author_from_text(text: str) -> str:
    """Extract author name from title string with enhanced patterns."""
    if not text:
        return ""
    
    patterns = [
        # Enhanced Chinese patterns with more specific matching
        r'作者[：:]\s*([^,;()【】《》\n]+?)(?:\s*[,;()【】《》\n]|$)',
        r'author[：:]\s*([^,;()【】《》\n]+?)(?:\s*[,;()【】《》\n]|$)',
        r'([^,;()【】《》\s]+?)\s*著\s*$',
        r'([^,;()【】《》\s]+?)\s*著作?\s*$',
        r'([^,;()【】《》]+?)\s*[编編写寫]\s*$',
        r'：\s*([^,;()【】《》]+?)\s*著?\s*$',
        
        # English patterns
        r'by\s+([^,;()【】《》\n]+?)(?:\s*[,;()【】《》\n]|$)',
        r'written\s+by\s+([^,;()【】《》\n]+?)(?:\s*[,;()【】《》\n]|$)',
        r'authored?\s+by\s+([^,;()【】《》\n]+?)(?:\s*[,;()【】《》\n]|$)',
        
        # Parentheses and brackets
        r'\(([^)]+?)\)\s*$',
        r'【([^】]+?)】\s*$',
        r'《([^》]+?)》著',
        
        # Space-separated author patterns (more restrictive)
        r'\s+([A-Za-z]+(?:\s+[A-Za-z]+){1,3})\s*$',  # English names only
        r'\s+([\u4e00-\u9fff]{2,4})\s*$',  # Chinese names only
        
        # Colon/dash separated
        r'[：:\-–—]\s*([^,;()【】《》\n]+?)\s*$',
        
        # Comma separated with author indicators
        r'[,;]\s*([^,;()【】《》\n]+?)\s*(?:著|编|編|write|寫)\s*$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            author = match.group(1).strip()
            
            # Enhanced validation
            if (2 <= len(author) <= 50 and 
                not any(word in author.lower() for word in ['edition', '版', 'vol', 'series', 'translation', 'revised', 'updated', 'illustrated', 'complete']) and
                not any(char in author for char in [':', '：', '!', '?', '@', '#', '$', '%', '^', '&', '*']) and
                not re.search(r'\d{4}', author) and  # No years
                not re.search(r'(第\d+版|edition|press|publishing)', author, re.IGNORECASE)):
                
                # Clean up
                author = re.sub(r'^(作者|by|author)\s*[：:]*\s*', '', author, flags=re.IGNORECASE)
                author = re.sub(r'\s*(著|编|編|write|寫|译|譯)$', '', author)
                author = re.sub(r'\s*(press|publishing|publisher)$', '', author, flags=re.IGNORECASE)
                author = author.strip()
                
                if len(author) >= 2:
                    return author
    
    return ""


def enhanced_book_similarity(reference_book: Union[Dict, str], comparison_book: Union[Dict, str]) -> Dict[str, float]:
    """Enhanced similarity calculation considering all book metadata."""
    # Handle both dict and string inputs
    if isinstance(reference_book, str):
        reference_book = {"title": reference_book}
    if isinstance(comparison_book, str):
        comparison_book = {"title": comparison_book}
    
    # Extract data with None handling
    ref_title = reference_book.get("title", "") or ""
    comp_title = comparison_book.get("title", "") or ""
    ref_author = reference_book.get("author") or ""
    comp_author = comparison_book.get("author") or ""
    ref_language = (reference_book.get("language") or "").lower().strip()
    comp_language = (comparison_book.get("language") or "").lower().strip()
    ref_file_type = (reference_book.get("file_type") or "").lower().strip()
    comp_file_type = (comparison_book.get("file_type") or "").lower().strip()
    
    # Extract authors from title if not provided
    if not ref_author:
        ref_author = extract_author_from_text(ref_title) or ""
    if not comp_author:
        comp_author = extract_author_from_text(comp_title) or ""
    
    basic_scores = similarities(ref_title, comp_title)
    
    # Author similarity
    author_score = 0.0
    if ref_author and comp_author:
        ref_author_clean = normalize_author_name(ref_author)
        comp_author_clean = normalize_author_name(comp_author)
        
        if ref_author_clean and comp_author_clean:
            author_score = calculate_author_similarity(ref_author_clean, comp_author_clean)
    
    # Language and file type matching
    language_bonus = 0.0
    if ref_language and comp_language:
        language_bonus = 1.0 if ref_language == comp_language else 0.0
    
    file_type_bonus = 0.0
    if ref_file_type and comp_file_type:
        file_type_bonus = 1.0 if ref_file_type == comp_file_type else 0.0
    
    # Pattern analysis
    translation_bonus = detect_translation_pair(ref_title, comp_title, ref_language, comp_language)
    edition_bonus = detect_edition_variation(ref_title, comp_title)
    regional_penalty = detect_regional_variation(ref_title, comp_title)
    
    return {
        **basic_scores,
        "author_similarity": author_score,
        "language_match": language_bonus,
        "file_type_match": file_type_bonus,
        "translation_bonus": translation_bonus,
        "edition_bonus": edition_bonus,
        "regional_penalty": regional_penalty
    }


def normalize_author_name(author: str) -> str:
    """Normalize author names for better comparison with enhanced cleaning."""
    if not author:
        return ""
    
    # Remove common prefixes/suffixes
    author = re.sub(r'^(dr\.?|prof\.?|professor|mr\.?|ms\.?|mrs\.?)\s+', '', author, flags=re.IGNORECASE)
    author = re.sub(r'\s+(jr\.?|sr\.?|iii?|iv|phd|md|esq)\.?$', '', author, flags=re.IGNORECASE)
    
    # Remove translator/editor annotations more aggressively
    author = re.sub(r'\s*[；;]\s*.*?[译譯编編著写寫].*$', '', author)
    author = re.sub(r'\s*\([^)]*[译譯编編著写寫][^)]*\).*$', '', author)
    author = re.sub(r'\s*\[[^\]]*[译譯编編著写寫][^\]]*\].*$', '', author)
    
    # Remove publisher/press info
    author = re.sub(r'\s*(press|publishing|publisher|出版社|社).*$', '', author, flags=re.IGNORECASE)
    
    # Normalize spaces and punctuation
    author = re.sub(r'[·・\.]', ' ', author)
    author = re.sub(r'[,，]', ' ', author)  # Remove commas
    author = re.sub(r'\s+', ' ', author)
    
    # Remove extra parentheses content if it looks like metadata
    author = re.sub(r'\s*\([^)]*(?:born|died|\d{4}|country|nation)[^)]*\)', '', author, flags=re.IGNORECASE)
    
    return author.strip()


def calculate_author_similarity(author1: str, author2: str) -> float:
    """Calculate specialized author similarity with enhanced pattern matching and higher bar."""
    if not author1 or not author2:
        return 0.0
    
    norm1, norm2 = normalize_author_name(author1), normalize_author_name(author2)
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1.lower() == norm2.lower():
        return 1.0
    
    parts1, parts2 = norm1.lower().split(), norm2.lower().split()
    
    # Single word names - use strict similarity
    if len(parts1) <= 1 or len(parts2) <= 1:
        text_sim = similarities(norm1, norm2)['token_set_ratio']
        return text_sim if text_sim >= 0.8 else 0.0  # Higher threshold
    
    score = 0.0
    
    # Enhanced name pattern matching
    if len(parts1) >= 2 and len(parts2) >= 2:
        last1, last2 = parts1[-1], parts2[-1]
        first1, first2 = parts1[0], parts2[0]
        
        # Last name exact match
        if last1 == last2:
            score += 0.7  # Increased base score for exact last name match
            
            # First name matching with enhanced patterns
            if first1 == first2:
                score += 0.3  # Perfect match
            elif (len(first1) >= 1 and len(first2) >= 1 and first1[0] == first2[0]):
                # Initial matching
                if (first1.rstrip('.') == first2.rstrip('.') or 
                    first1.startswith(first2.rstrip('.')) or 
                    first2.startswith(first1.rstrip('.'))):
                    score += 0.25
                else:
                    score += 0.15  # Just initial match
        
        # Check for middle names/initials
        if score >= 0.7 and len(parts1) >= 3 and len(parts2) >= 3:
            # Compare middle parts
            middle1 = ' '.join(parts1[1:-1])
            middle2 = ' '.join(parts2[1:-1])
            if middle1 and middle2:
                if middle1 == middle2:
                    score = min(1.0, score + 0.05)
                elif (middle1[0] == middle2[0] if len(middle1) > 0 and len(middle2) > 0 else False):
                    score = min(1.0, score + 0.02)
        
        # Check for name order reversal (stricter)
        elif len(parts1) == 2 and len(parts2) == 2:
            if parts1[0] == parts2[1] and parts1[1] == parts2[0]:
                score = 0.95
        
        # Check for transliteration patterns (Chinese-English)
        elif is_likely_transliteration(norm1, norm2):
            score = 0.75  # Good confidence for transliterations
    
    # Fallback to text similarity only if no good pattern match and strict threshold
    if score < 0.5:
        text_sims = similarities(norm1, norm2)
        fallback_score = (text_sims['token_set_ratio'] * 0.4 + 
                         text_sims['token_sort_ratio'] * 0.3 + 
                         text_sims['jaro_winkler'] * 0.3)
        # Only use fallback if it's very high
        if fallback_score >= 0.85:
            score = max(score, fallback_score * 0.8)  # Reduce fallback confidence
    
    return min(1.0, score)


def is_likely_transliteration(name1: str, name2: str) -> bool:
    """Check if two names are likely transliterations of each other."""
    def has_chinese(text): return any('\u4e00' <= char <= '\u9fff' for char in text)
    def has_latin(text): return any('a' <= char.lower() <= 'z' for char in text)
    
    # One Chinese, one Latin
    if (has_chinese(name1) and has_latin(name2)) or (has_latin(name1) and has_chinese(name2)):
        # Simple length and structure checks
        chinese_name = name1 if has_chinese(name1) else name2
        latin_name = name2 if has_chinese(name1) else name1
        
        # Chinese names are typically 2-4 characters
        if 2 <= len(chinese_name) <= 4 and 3 <= len(latin_name) <= 25:
            return True
    
    return False


def detect_translation_pair(title1: str, title2: str, lang1: str = "", lang2: str = "") -> float:
    """Detect if two titles are likely translations. Returns bonus score (0.0 to 0.5)."""
    lang1, lang2 = (lang1 or "").strip().lower(), (lang2 or "").strip().lower()
    
    translation_patterns = [
        r'=\s*[^=]+$', r'：[^：]+$', r'\([^)]*[a-zA-Z][^)]*\)$', r'\[[^\]]*[a-zA-Z][^\]]*\]$'
    ]
    
    has_pattern = any(re.search(p, title1) or re.search(p, title2) for p in translation_patterns)
    different_langs = (lang1 and lang2 and lang1 != lang2)
    
    def has_chinese(text): return any('\u4e00' <= char <= '\u9fff' for char in text)
    def has_english(text): return any(char.isalpha() and ord(char) < 128 for char in text)
    
    chinese_english = ((has_chinese(title1) and has_english(title2)) or 
                       (has_english(title1) and has_chinese(title2)))
    
    bonus = 0.0
    if has_pattern: bonus += 0.3
    if different_langs: bonus += 0.2
    if chinese_english: bonus += 0.2
    
    return min(bonus, 0.5)


def detect_edition_variation(title1: str, title2: str) -> float:
    """Detect if titles are different editions of the same book."""
    edition_keywords = [
        r'第\d+版', r'\d+th\s+edition', r'\d+nd\s+edition', r'\d+rd\s+edition', r'\d+st\s+edition',
        r'revised\s+edition', r'updated\s+edition', r'新版', r'修订版', r'增订版',
        r'anniversary\s+edition', r'纪念版', r'commemorative',
        r'illustrated\s+edition', r'插图版', r'图解版',
        r'deluxe\s+edition', r'精装版', r'豪华版'
    ]
    
    title1_core, title2_core = title1, title2
    
    for pattern in edition_keywords:
        title1_core = re.sub(pattern, '', title1_core, flags=re.IGNORECASE)
        title2_core = re.sub(pattern, '', title2_core, flags=re.IGNORECASE)
    
    title1_core = re.sub(r'\s*[\(\[\)]\s*', ' ', title1_core)
    title2_core = re.sub(r'\s*[\(\[\)]\s*', ' ', title2_core)
    title1_core = re.sub(r'\s+', ' ', title1_core).strip()
    title2_core = re.sub(r'\s+', ' ', title2_core).strip()
    
    if title1_core and title2_core:
        core_similarity = get_best_match_score(title1_core, title2_core)
        if core_similarity > 0.85:
            return 0.3
    
    return 0.0


def detect_regional_variation(title1: str, title2: str) -> float:
    """Detect regional variations (US vs UK). Returns penalty (0.0 to 0.15)."""
    # Skip penalty for identical matches
    if title1 == title2:
        return 0.0
    
    title1_norm, title2_norm = normalize(title1), normalize(title2)
    
    # Skip penalty for identical normalized matches
    if title1_norm == title2_norm:
        return 0.0
    
    regional_variations = [
        (r"philosopher'?s?\s+stone", r"sorcerer'?s?\s+stone"),
        (r"\bcolor\b", r"\bcolour\b"), (r"\bfavor\b", r"\bfavour\b"),
        (r"\bhonor\b", r"\bhonour\b"), (r"\blabor\b", r"\blabour\b"),
        (r"organize", r"organise"), (r"realize", r"realise"), (r"analyze", r"analyse"),
        (r"\bcenter\b", r"\bcentre\b"), (r"\btheater\b", r"\btheatre\b"),
        (r"\bgray\b", r"\bgrey\b"), (r"\btires?\b", r"\btyres?\b"),
        (r"\bdefense\b", r"\bdefence\b"), (r"\blicense\b", r"\blicence\b"),
    ]
    
    # Check if differences are due to regional variations
    for pattern1, pattern2 in regional_variations:
        # Convert pattern1 in title1 to pattern2 and see if it matches title2
        temp1_converted = re.sub(pattern1, lambda m: re.sub(pattern1, pattern2.replace('\\b', ''), m.group(0), flags=re.IGNORECASE), 
                               title1_norm, flags=re.IGNORECASE)
        # Convert pattern2 in title2 to pattern1 and see if it matches title1  
        temp2_converted = re.sub(pattern2, lambda m: re.sub(pattern2, pattern1.replace('\\b', ''), m.group(0), flags=re.IGNORECASE), 
                               title2_norm, flags=re.IGNORECASE)
        
        if ((temp1_converted != title1_norm and temp1_converted == title2_norm) or
            (temp2_converted != title2_norm and temp2_converted == title1_norm)):
            return 0.15
    
    # Check for minor word differences that might indicate regional variations
    words1, words2 = set(title1_norm.split()), set(title2_norm.split())
    
    if (len(words1) == len(words2) and len(words1) > 2):
        different_words = words1.symmetric_difference(words2)
        common_words = words1.intersection(words2)
        
        if len(different_words) <= 2 and len(common_words) >= len(words1) * 0.8:
            return 0.10
    
    return 0.0


def comprehensive_book_similarity_score(reference_book: Union[Dict, str], comparison_book: Union[Dict, str]) -> float:
    """Calculate comprehensive similarity score with enhanced author-centric approach and higher bar."""
    scores = enhanced_book_similarity(reference_book, comparison_book)
    
    # Adjusted weights - reduced base text weights to make room for stricter logic
    base_weights = {
        'levenshtein_ratio': 0.06,
        'token_sort_ratio': 0.10,
        'token_set_ratio': 0.10,
        'jaro_winkler': 0.06,
        'semantic_similarity': 0.08,
    }
    
    # Enhanced metadata weights with higher author emphasis
    metadata_weights = {
        'author_similarity': 0.55,  # Increased from 0.50
        'language_match': 0.015,
        'file_type_match': 0.005,
        'translation_bonus': 0.015,
        'edition_bonus': 0.015,
    }
    
    base_score = sum(scores[metric] * weight for metric, weight in base_weights.items())
    metadata_score = sum(scores[metric] * weight for metric, weight in metadata_weights.items())
    total_score = base_score + metadata_score
    
    author_similarity = scores.get('author_similarity', 0)
    
    # Apply regional penalty with enhanced author adjustment
    regional_penalty = scores.get('regional_penalty', 0)
    if regional_penalty > 0:
        if author_similarity > 0.9:
            regional_penalty *= 0.1  # Almost no penalty for very strong author match
        elif author_similarity > 0.8:
            regional_penalty *= 0.2
        elif author_similarity > 0.6:
            regional_penalty *= 0.5
        total_score = max(0.0, total_score - regional_penalty)
    
    # Enhanced author-based logic with higher bar
    if author_similarity > 0.9:  # Very strong author match
        total_score = min(1.0, total_score * 1.25)
        max_title_score = max(scores.get(k, 0) for k in ['token_set_ratio', 'token_sort_ratio', 'semantic_similarity'])
        if max_title_score > 0.5:  # Even moderate title similarity gets boost
            total_score = min(1.0, total_score * 1.1)
    elif author_similarity > 0.8:  # Strong author match
        total_score = min(1.0, total_score * 1.15)
        max_title_score = max(scores.get(k, 0) for k in ['token_set_ratio', 'token_sort_ratio', 'semantic_similarity'])
        if max_title_score > 0.6:
            total_score = min(1.0, total_score * 1.08)
    elif author_similarity > 0.6:  # Moderate author match
        total_score = min(1.0, total_score * 1.05)
    
    # Penalty for conflicting authors (when both authors are present but different)
    if author_similarity < 0.3 and author_similarity > 0:
        # Check if both books actually have author info
        ref_author = ""
        comp_author = ""
        if isinstance(reference_book, dict):
            ref_author = reference_book.get("author") or extract_author_from_text(reference_book.get("title", ""))
        if isinstance(comparison_book, dict):
            comp_author = comparison_book.get("author") or extract_author_from_text(comparison_book.get("title", ""))
        
        if ref_author and comp_author and len(ref_author) > 2 and len(comp_author) > 2:
            # Strong penalty for conflicting authors
            total_score *= 0.6
    
    # Translation boost with author confirmation
    translation_bonus = scores.get('translation_bonus', 0)
    if translation_bonus > 0.3:
        boost = 1.12 if author_similarity > 0.7 else 1.06
        total_score = min(1.0, total_score * boost)
    
    # High individual title score boost (more conservative)
    max_base_score = max(scores[metric] for metric in base_weights.keys())
    if max_base_score > 0.95:
        boost = 1.06 if author_similarity > 0.8 else 1.03
        total_score = min(1.0, total_score * boost)
    elif max_base_score > 0.9:
        boost = 1.04 if author_similarity > 0.8 else 1.02
        total_score = min(1.0, total_score * boost)
    
    # Author compensation for weak title match (more selective)
    if author_similarity > 0.9 and max_base_score < 0.4:
        compensation = min(0.2, author_similarity * 0.25)
        total_score = min(1.0, total_score + compensation)
    elif author_similarity > 0.85 and max_base_score < 0.3:
        compensation = min(0.15, author_similarity * 0.2)
        total_score = min(1.0, total_score + compensation)
    
    # Edition boost with author confirmation
    if scores.get('edition_bonus', 0) > 0.2 and author_similarity > 0.8:
        total_score = min(1.0, total_score * 1.05)
    
    # Conservative adjustment - prevent over-scoring on weak matches
    if author_similarity < 0.5 and max_base_score < 0.7:
        total_score *= 0.9
    
    return total_score


def find_best_book_matches(query_book: Union[Dict, str], candidate_books: List[Dict], 
                          top_k: int = 5, min_score: float = 0.4) -> List[Dict]:
    """Find the best matching books from candidates with enhanced filtering."""
    if not candidate_books:
        return []
    
    matches = []
    for candidate in candidate_books:
        score = comprehensive_book_similarity_score(query_book, candidate)
        
        # Enhanced filtering with author consideration
        if score >= min_score:
            # Additional quality check
            if isinstance(query_book, dict) and isinstance(candidate, dict):
                query_author = query_book.get("author") or extract_author_from_text(query_book.get("title", ""))
                candidate_author = candidate.get("author") or extract_author_from_text(candidate.get("title", ""))
                
                # If both have authors and they conflict strongly, lower the threshold
                if query_author and candidate_author:
                    author_sim = calculate_author_similarity(query_author, candidate_author)
                    if author_sim < 0.2 and score < 0.8:  # Strong author conflict with moderate score
                        continue  # Skip this match
            
            matches.append({
                'book': candidate,
                'score': score,
                'category': categorize_similarity(score)
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:top_k]


def categorize_similarity(score: float) -> str:
    """Categorize similarity score with adjusted thresholds."""
    if score >= 0.9: return "Excellent"  # More appropriate threshold for identical matches
    if score >= 0.7: return "Good"       # Good for clear matches
    if score >= 0.5: return "Moderate"   # Moderate for potential matches  
    return "Poor"


def find_best_matches(query: str, candidates: List[str], top_k: int = 5, min_score: float = 0.4) -> List[Dict]:
    """Find the best matching titles from candidates with enhanced filtering."""
    if not candidates:
        return []
    
    matches = []
    for candidate in candidates:
        score = get_best_match_score(query, candidate)
        
        if score >= min_score:
            matches.append({
                'title': candidate,
                'score': score,
                'category': categorize_similarity(score)
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:top_k]


def batch_similarity_matrix(titles: List[str]) -> np.ndarray:
    """Calculate similarity matrix for a batch of titles."""
    n = len(titles)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[i][j] = 1.0
            else:
                score = get_best_match_score(titles[i], titles[j])
                matrix[i][j] = matrix[j][i] = score
    
    return matrix


def suggest_corrections(query: str, candidates: List[str], threshold: float = 0.5) -> List[str]:
    """Suggest possible corrections for a query title based on candidates."""
    matches = find_best_matches(query, candidates, top_k=10, min_score=threshold)
    return [match['title'] for match in matches if match['score'] < 0.9]


def analyze_match_reasons(scores: Dict[str, float]) -> List[str]:
    """Return primary match reason with enhanced logic."""
    reasons = []
    
    if scores.get('author_similarity', 0) > 0.8:
        reasons.append("Strong author match")
    elif scores.get('author_similarity', 0) > 0.6:
        reasons.append("Moderate author match")
    
    if scores.get('token_set_ratio', 0) > 0.9:
        reasons.append("High title similarity")
    elif scores.get('token_sort_ratio', 0) > 0.9:
        reasons.append("High title similarity (reordered)")
    
    if scores.get('translation_bonus', 0) > 0.2:
        reasons.append("Translation pair")
    
    if scores.get('semantic_similarity', 0) > 0.8:
        reasons.append("High semantic similarity")
    
    if scores.get('edition_bonus', 0) > 0.2:
        reasons.append("Edition variation")
    
    return reasons if reasons else ["Basic similarity"]


def get_best_match_score(title1: str, title2: str) -> float:
    """Get comprehensive similarity score between two titles."""
    return comprehensive_similarity_score(title1, title2)
