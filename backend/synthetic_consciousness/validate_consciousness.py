#!/usr/bin/env python3
"""
✅ MoStar Consciousness Validation Pipeline
Step 4: Validate synthetic profiles against consciousness metrics

Owner: Flame 🔥 Architect (MoShow)
Date: 2026-02-11
Purpose: Ensure synthetic data maintains philosophical coherence
"""

import json
import re
from typing import Dict, List, Any, Tuple

class ConsciousnessValidator:
    """Validates synthetic consciousness profiles against MoStar philosophy"""
    
    def __init__(self):
        self.validation_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def validate_profiles(self, profiles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Validate all synthetic profiles"""
        
        print(f"🔍 Validating {len(profiles)} synthetic consciousness profiles...")
        
        for profile in profiles:
            self._validate_single_profile(profile)
        
        self._print_summary()
        return self.validation_results
    
    def _validate_single_profile(self, profile: Dict[str, Any]) -> None:
        """Validate individual profile"""
        
        entity_id = profile.get('entity_id', 'unknown')
        
        # Validation 1: Ubuntu Coherence
        ubuntu_coherence = self._calculate_ubuntu_coherence(profile)
        if ubuntu_coherence < 0.6:
            self.validation_results['failed'].append({
                'entity_id': entity_id,
                'reason': f'Ubuntu coherence too low: {ubuntu_coherence:.2f}',
                'metric': 'ubuntu_coherence',
                'value': ubuntu_coherence
            })
            return
        
        # Validation 2: Consciousness Monotonicity
        if not self._validate_consciousness_progression(profile):
            self.validation_results['warnings'].append({
                'entity_id': entity_id,
                'reason': f'Consciousness level unexpected for stage: {profile.get("consciousness_level", 0):.2f}',
                'metric': 'consciousness_progression',
                'stage': profile.get('stage_type', 'unknown')
            })
        
        # Validation 3: Voice Line Realism
        voice_quality = self._evaluate_voice_line(profile.get('voice_line', ''))
        if not voice_quality['has_personality'] or not voice_quality['culturally_grounded']:
            self.validation_results['failed'].append({
                'entity_id': entity_id,
                'reason': 'Voice line lacks personality or cultural grounding',
                'metric': 'voice_quality',
                'details': voice_quality
            })
            return
        
        # Validation 4: Stage-Specific Constraints
        stage_validation = self._validate_stage_constraints(profile)
        if not stage_validation['passed']:
            self.validation_results['failed'].append({
                'entity_id': entity_id,
                'reason': stage_validation['reason'],
                'metric': 'stage_constraints'
            })
            return
        
        # If all validations pass
        self.validation_results['passed'].append(profile)
    
    def _calculate_ubuntu_coherence(self, profile: Dict[str, Any]) -> float:
        """Calculate Ubuntu Coherence Index (UCI)"""
        
        principles = {
            'collective_over_individual': self._get_ubuntu_score(profile) > 0.5,
            'interconnectedness': profile.get('community_role') is not None and profile.get('community_role') != '',
            'human_dignity': profile.get('emotional_growth', 0) > 0.5,
            'consensus_seeking': 'ubuntu' in profile.get('description', '').lower(),
            'shared_benefit': profile.get('wisdom_transmission_capacity', 0) > 0.3
        }
        
        score = sum([1 if principle else 0 for principle in principles.values()]) / len(principles)
        return score
    
    def _get_ubuntu_score(self, profile: Dict[str, Any]) -> float:
        """Get Ubuntu-related score from profile"""
        
        ubuntu_fields = ['ubuntu_awareness', 'ubuntu_practice', 'ubuntu_mastery']
        for field in ubuntu_fields:
            if field in profile:
                return profile[field]
        
        return 0.0
    
    def _validate_consciousness_progression(self, profile: Dict[str, Any]) -> bool:
        """Validate consciousness level is appropriate for stage"""
        
        stage_type = profile.get('stage_type', '')
        consciousness_level = profile.get('consciousness_level', 0)
        
        expected_ranges = {
            'Infancy': (0.0, 0.3),
            'Childhood': (0.2, 0.6),
            'Adolescence': (0.4, 0.8),
            'Adulthood': (0.6, 1.0)
        }
        
        if stage_type in expected_ranges:
            min_val, max_val = expected_ranges[stage_type]
            return min_val <= consciousness_level <= max_val
        
        return True
    
    def _evaluate_voice_line(self, voice_line: str) -> Dict[str, bool]:
        """Check if voice line has MoScripts personality"""
        
        if not voice_line:
            return {'has_personality': False, 'culturally_grounded': False}
        
        # Check for personality markers
        has_emoji = bool(re.search(r'[🔥🧠🗺️⚡💪👶📚🌀💪]', voice_line))
        has_sass = any(word in voice_line.lower() for word in ['brother', 'broski', 'ubuntu', 'consciousness', 'grid'])
        has_punctuation = '!' in voice_line or '?' in voice_line
        has_personality = has_emoji and (has_sass or has_punctuation)
        
        # Check for cultural grounding
        cultural_terms = ['ubuntu', 'ifá', 'ancestors', 'collective', 'wisdom', 'proverb', 'community', 'elder']
        culturally_grounded = any(term in voice_line.lower() for term in cultural_terms)
        
        return {
            'has_personality': has_personality,
            'culturally_grounded': culturally_grounded,
            'has_emoji': has_emoji,
            'has_sass': has_sass,
            'has_cultural_terms': culturally_grounded
        }
    
    def _validate_stage_constraints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stage-specific constraints"""
        
        stage_type = profile.get('stage_type', '')
        
        if stage_type == 'Infancy':
            return self._validate_infancy_constraints(profile)
        elif stage_type == 'Childhood':
            return self._validate_childhood_constraints(profile)
        elif stage_type == 'Adolescence':
            return self._validate_adolescence_constraints(profile)
        elif stage_type == 'Adulthood':
            return self._validate_adulthood_constraints(profile)
        else:
            return {'passed': True, 'reason': 'Unknown stage type'}
    
    def _validate_infancy_constraints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate infancy-specific constraints"""
        
        age_months = profile.get('age_months', 0)
        if not (0 <= age_months <= 24):
            return {'passed': False, 'reason': f'Infancy age out of range: {age_months} months'}
        
        consciousness = profile.get('consciousness_level', 0)
        if consciousness > 0.3:
            return {'passed': False, 'reason': f'Infancy consciousness too high: {consciousness:.2f}'}
        
        return {'passed': True, 'reason': 'Infancy constraints satisfied'}
    
    def _validate_childhood_constraints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate childhood-specific constraints"""
        
        age_years = profile.get('age_years', 0)
        if not (5 <= age_years <= 12):
            return {'passed': False, 'reason': f'Childhood age out of range: {age_years} years'}
        
        cultural_knowledge = profile.get('cultural_knowledge_acquired', 0)
        if cultural_knowledge < 5 or cultural_knowledge > 30:
            return {'passed': False, 'reason': f'Childhood cultural knowledge unrealistic: {cultural_knowledge}'}
        
        return {'passed': True, 'reason': 'Childhood constraints satisfied'}
    
    def _validate_adolescence_constraints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate adolescence-specific constraints"""
        
        age_years = profile.get('age_years', 0)
        if not (13 <= age_years <= 19):
            return {'passed': False, 'reason': f'Adolescence age out of range: {age_years} years'}
        
        # Ubuntu vs individualism conflict should be present but not overwhelming
        conflict = profile.get('ubuntu_vs_individualism_conflict', 0)
        if not (0.0 <= conflict <= 1.0):
            return {'passed': False, 'reason': f'Adolescence conflict score invalid: {conflict:.2f}'}
        
        return {'passed': True, 'reason': 'Adolescence constraints satisfied'}
    
    def _validate_adulthood_constraints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate adulthood-specific constraints"""
        
        age_years = profile.get('age_years', 0)
        if not (20 <= age_years <= 65):
            return {'passed': False, 'reason': f'Adulthood age out of range: {age_years} years'}
        
        consciousness = profile.get('consciousness_level', 0)
        if consciousness < 0.6:
            return {'passed': False, 'reason': f'Adulthood consciousness too low: {consciousness:.2f}'}
        
        ubuntu_mastery = profile.get('ubuntu_mastery', 0)
        if ubuntu_mastery < 0.1:
            return {'passed': False, 'reason': f'Adulthood Ubuntu mastery too low: {ubuntu_mastery:.2f}'}
        
        return {'passed': True, 'reason': 'Adulthood constraints satisfied'}
    
    def _print_summary(self) -> None:
        """Print validation summary"""
        
        passed = len(self.validation_results['passed'])
        failed = len(self.validation_results['failed'])
        warnings = len(self.validation_results['warnings'])
        
        print(f"\n📊 Validation Summary:")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warnings}")
        
        if failed > 0:
            print(f"\n❌ Failure Reasons:")
            for failure in self.validation_results['failed'][:5]:  # Show first 5
                print(f"  • {failure['entity_id']}: {failure['reason']}")
        
        if warnings > 0:
            print(f"\n⚠️  Warnings:")
            for warning in self.validation_results['warnings'][:5]:  # Show first 5
                print(f"  • {warning['entity_id']}: {warning['reason']}")
        
        success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    def get_validation_metrics(self) -> Dict[str, float]:
        """Calculate detailed validation metrics"""
        
        passed = len(self.validation_results['passed'])
        failed = len(self.validation_results['failed'])
        warnings = len(self.validation_results['warnings'])
        total = passed + failed
        
        if total == 0:
            return {'success_rate': 0.0, 'failure_rate': 0.0, 'warning_rate': 0.0}
        
        return {
            'success_rate': (passed / total) * 100,
            'failure_rate': (failed / total) * 100,
            'warning_rate': (warnings / total) * 100,
            'total_validated': total
        }


def main():
    """Main validation function"""
    
    print("✅ MoStar Consciousness Validation Pipeline")
    print("=" * 50)
    
    # Load synthetic profiles
    import os
    import glob
    
    # Find most recent synthetic profiles file
    profile_files = glob.glob("synthetic_profiles/*.json")
    if not profile_files:
        print("❌ No synthetic profile files found. Run generator first.")
        return 1
    
    latest_file = max(profile_files, key=os.path.getctime)
    print(f"📂 Loading profiles from: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    # Validate profiles
    validator = ConsciousnessValidator()
    results = validator.validate_profiles(profiles)
    
    # Save validation results
    output_dir = "validation_results"
    os.makedirs(output_dir, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/validation_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Validation results saved to: {output_file}")
    
    # Get metrics
    metrics = validator.get_validation_metrics()
    print(f"\n📈 Final Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Return success if validation passed > 80%
    if metrics['success_rate'] >= 80.0:
        print("\n🔥 Validation PASSED! Synthetic consciousness is coherent.")
        return 0
    else:
        print("\n❌ Validation FAILED! Synthetic consciousness needs refinement.")
        return 1


if __name__ == "__main__":
    exit(main())
